#!/usr/bin/env python3
"""
Console File Manager with Panel System
Консольный файловый менеджер с панельной системой
"""

import os
import sys
import curses
import stat
import shutil
import mimetypes
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import subprocess

from ui_library import PanelManager, PanelState, PanelType


class FileManager:
    """Основной класс файлового менеджера"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.panel_manager = PanelManager(stdscr)
        self.clipboard = []
        self.clipboard_operation = None  # 'copy' or 'cut'
        self.bookmarks = {}
        self.history = []
        self.config = self._load_config()

        # Регистрация обработчиков команд
        self._register_command_handlers()

        # Регистрация обработчиков функциональных клавиш
        self._setup_function_keys()

        # Начальная директория
        start_path = os.getcwd()
        self._open_directory(start_path)

    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации"""
        default_config = {
            'show_hidden': False,
            'follow_symlinks': True,
            'confirm_delete': True,
            'editor': os.environ.get('EDITOR', 'nano'),
            'auto_preview': True
        }

        config_path = Path.home() / '.filemanager_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception:
                pass

        return default_config

    def _save_config(self):
        """Сохранение конфигурации"""
        config_path = Path.home() / '.filemanager_config.json'
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _register_command_handlers(self):
        """Регистрация обработчиков команд"""
        handlers = {
            'cd': self._cmd_cd,
            'ls': self._cmd_ls,
            'pwd': self._cmd_pwd,
            'find': self._cmd_find,
            'grep': self._cmd_grep,
            'tree': self._cmd_tree,
            'bookmark': self._cmd_bookmark,
            'history': self._cmd_history,
            'close': self._cmd_close,
            'branch': self._cmd_branch,
            'config': self._cmd_config,
            'help': self._cmd_help,
            'quit': self._cmd_quit,
            'exit': self._cmd_quit
        }

        for cmd, handler in handlers.items():
            self.panel_manager.register_command_handler(cmd, handler)

    def _setup_function_keys(self):
        """Настройка функциональных клавиш"""
        current_panel = self.panel_manager.get_current_panel()
        if not current_panel:
            return

        if current_panel.state.panel_type == PanelType.DIRECTORY:
            keys = {
                'F1': 'Help',
                'F2': 'Rename',
                'F3': 'View',
                'F4': 'Edit',
                'F5': 'Copy',
                'F6': 'Move',
                'F7': 'Mkdir',
                'F8': 'Delete',
                'F10': 'Quit'
            }
        elif current_panel.state.panel_type == PanelType.FILE:
            keys = {
                'F1': 'Help',
                'F2': 'Rename',
                'F3': 'Mode',
                'F4': 'Edit',
                'F5': 'Copy',
                'F7': 'Search',
                'F8': 'Close',
                'F10': 'Quit'
            }
        elif current_panel.state.panel_type == PanelType.ARCHIVE:
            keys = {
                'F1': 'Help',
                'F4': 'Extract',
                'F5': 'ExtractAll',
                'F6': 'Add',
                'F8': 'Delete',
                'F10': 'Quit'
            }
        else:
            keys = {'F10': 'Quit'}

        self.panel_manager.function_keys.set_keys(keys)

    def _get_file_icon(self, path: Path, is_dir: bool = False) -> str:
        """Получение иконки для файла"""
        if is_dir:
            return '[DIR]'

        suffix = path.suffix.lower()

        # Архивы
        if suffix in ['.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar']:
            return '[ARC]'
        # Изображения
        elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico']:
            return '[IMG]'
        # Код
        elif suffix in ['.py', '.js', '.html', '.css', '.c', '.cpp', '.java', '.go', '.rs']:
            return '[CODE]'
        # Исполняемые файлы
        elif os.access(path, os.X_OK) and not is_dir:
            return '[EXE]'
        else:
            return '[FILE]'

    def _format_size(self, size: int) -> str:
        """Форматирование размера файла"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"

    def _format_permissions(self, mode: int) -> str:
        """Форматирование прав доступа"""
        perms = stat.filemode(mode)
        return perms

    def _get_directory_content(self, path: Path) -> List[str]:
        """Получение содержимого директории"""
        try:
            items = []
            entries = list(path.iterdir())

            # Сортировка: сначала директории, потом файлы
            entries.sort(key=lambda x: (not x.is_dir(), x.name.lower()))

            for entry in entries:
                # Скрытые файлы
                if entry.name.startswith('.') and not self.config['show_hidden']:
                    continue

                try:
                    stat_info = entry.stat()
                    is_dir = entry.is_dir()

                    icon = self._get_file_icon(entry, is_dir)
                    name = entry.name

                    if is_dir:
                        size_str = "<DIR>"
                    else:
                        size_str = self._format_size(stat_info.st_size)

                    modified = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M')

                    # Форматирование строки
                    line = f"{icon} {name:<30} {size_str:>10} {modified}"
                    items.append(line)

                except (OSError, PermissionError):
                    # Файл недоступен
                    icon = self._get_file_icon(entry, entry.is_dir())
                    line = f"{icon} {entry.name:<30} {'<PERM>':>10} {'':>16}"
                    items.append(line)

            return items

        except PermissionError:
            return ["Permission denied"]
        except Exception as e:
            return [f"Error: {str(e)}"]

    def _get_file_content(self, path: Path) -> List[str]:
        """Получение содержимого файла"""
        try:
            # Проверка размера файла
            stat_info = path.stat()
            if stat_info.st_size > 1024 * 1024:  # 1MB
                return [f"File too large: {self._format_size(stat_info.st_size)}",
                        "Use F4 to edit in external editor"]

            # Попытка прочитать как текст
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Ограничиваем количество строк
                    if len(lines) > 1000:
                        lines = lines[:1000] + ["... (file truncated)"]
                    return [line.rstrip('\n\r') for line in lines]
            except UnicodeDecodeError:
                # Бинарный файл - показываем hex дамп
                with open(path, 'rb') as f:
                    data = f.read(512)  # Первые 512 байт
                    lines = []
                    for i in range(0, len(data), 16):
                        chunk = data[i:i + 16]
                        hex_part = ' '.join(f'{b:02x}' for b in chunk)
                        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
                        lines.append(f"{i:08x}: {hex_part:<48} {ascii_part}")
                    if len(data) == 512:
                        lines.append("... (showing first 512 bytes)")
                    return lines

        except PermissionError:
            return ["Permission denied"]
        except Exception as e:
            return [f"Error reading file: {str(e)}"]

    def _get_archive_content(self, path: Path) -> List[str]:
        """Получение содержимого архива"""
        try:
            items = []

            if path.suffix.lower() == '.zip':
                with zipfile.ZipFile(path, 'r') as zf:
                    for info in zf.infolist():
                        if info.is_dir():
                            icon = '📁'
                            size_str = "<DIR>"
                        else:
                            icon = '📄'
                            size_str = self._format_size(info.file_size)

                        modified = datetime(*info.date_time).strftime('%Y-%m-%d %H:%M')
                        line = f"{icon} {info.filename:<40} {size_str:>10} {modified}"
                        items.append(line)

            elif path.suffix.lower() in ['.tar', '.tar.gz', '.tar.bz2', '.tar.xz']:
                with tarfile.open(path, 'r') as tf:
                    for member in tf.getmembers():
                        if member.isdir():
                            icon = '📁'
                            size_str = "<DIR>"
                        else:
                            icon = '📄'
                            size_str = self._format_size(member.size)

                        modified = datetime.fromtimestamp(member.mtime).strftime('%Y-%m-%d %H:%M')
                        line = f"{icon} {member.name:<40} {size_str:>10} {modified}"
                        items.append(line)
            else:
                return ["Unsupported archive format"]

            return items

        except Exception as e:
            return [f"Error reading archive: {str(e)}"]

    def _open_directory(self, path: str):
        """Открытие директории в новой панели"""
        try:
            dir_path = Path(path).resolve()
            if not dir_path.exists():
                return

            if not dir_path.is_dir():
                # Если это файл - открываем его содержимое
                self._open_file(dir_path)
                return

            content = self._get_directory_content(dir_path)

            # Подсчёт элементов
            item_count = len([line for line in content if not line.startswith("Error")])

            state = PanelState(
                title=str(dir_path),
                content=content,
                panel_type=PanelType.DIRECTORY,
                metadata={
                    'path': str(dir_path),
                    'items': item_count
                }
            )

            self.panel_manager.add_panel(state)
            self._setup_function_keys()

            # Добавляем в историю
            if str(dir_path) not in self.history:
                self.history.append(str(dir_path))
                if len(self.history) > 50:  # Ограничиваем историю
                    self.history.pop(0)

        except Exception as e:
            self._show_error(f"Cannot open directory: {str(e)}")

    def _open_file(self, path: Path):
        """Открытие файла в новой панели"""
        try:
            if not path.exists() or not path.is_file():
                return

            # Определяем тип файла
            if path.suffix.lower() in ['.zip', '.tar', '.tar.gz', '.tar.bz2', '.tar.xz']:
                # Архив
                content = self._get_archive_content(path)
                panel_type = PanelType.ARCHIVE
                title = f"📦 {path.name}"
            else:
                # Обычный файл
                content = self._get_file_content(path)
                panel_type = PanelType.FILE
                title = f"📄 {path.name}"

            # Получаем информацию о файле
            stat_info = path.stat()
            file_size = self._format_size(stat_info.st_size)

            state = PanelState(
                title=title,
                content=content,
                panel_type=panel_type,
                metadata={
                    'path': str(path),
                    'size': file_size,
                    'lines': len(content) if panel_type == PanelType.FILE else None
                }
            )

            self.panel_manager.add_panel(state)
            self._setup_function_keys()

        except Exception as e:
            self._show_error(f"Cannot open file: {str(e)}")

    def _show_error(self, message: str):
        """Показ сообщения об ошибке"""
        # Можно реализовать всплывающее окно или использовать статусную строку
        pass

    # Обработчики команд
    def _cmd_cd(self, args: List[str]):
        """Команда смены директории"""
        if not args:
            path = str(Path.home())
        else:
            path = ' '.join(args)

        # Разрешаем относительные пути
        current_panel = self.panel_manager.get_current_panel()
        if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
            current_path = Path(current_panel.state.metadata['path'])
            if not os.path.isabs(path):
                path = str(current_path / path)

        self._open_directory(path)

    def _cmd_ls(self, args: List[str]):
        """Команда обновления содержимого"""
        current_panel = self.panel_manager.get_current_panel()
        if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
            path = current_panel.state.metadata['path']
            # Обновляем содержимое текущей панели
            current_panel.state.content = self._get_directory_content(Path(path))

    def _cmd_pwd(self, args: List[str]):
        """Команда показа текущего пути"""
        current_panel = self.panel_manager.get_current_panel()
        if current_panel:
            path = current_panel.state.metadata.get('path', 'Unknown')
            # Показываем путь в командной строке
            self.panel_manager.command_line.text = path

    def _cmd_find(self, args: List[str]):
        """Команда поиска файлов"""
        if not args:
            return

        pattern = args[0]
        current_panel = self.panel_manager.get_current_panel()

        if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
            search_path = Path(current_panel.state.metadata['path'])

            try:
                results = []
                for root, dirs, files in os.walk(search_path):
                    # Поиск в именах файлов
                    for file in files:
                        if pattern.lower() in file.lower():
                            full_path = Path(root) / file
                            relative_path = full_path.relative_to(search_path)
                            results.append(f"📄 {relative_path}")

                    # Поиск в именах директорий
                    for dir_name in dirs:
                        if pattern.lower() in dir_name.lower():
                            full_path = Path(root) / dir_name
                            relative_path = full_path.relative_to(search_path)
                            results.append(f"📁 {relative_path}")

                if results:
                    state = PanelState(
                        title=f"Search: {pattern}",
                        content=results,
                        panel_type=PanelType.DIRECTORY,
                        metadata={'search_results': True}
                    )
                    self.panel_manager.add_panel(state)
                else:
                    results = [f"No files found matching '{pattern}'"]
                    state = PanelState(
                        title=f"Search: {pattern}",
                        content=results,
                        panel_type=PanelType.FILE
                    )
                    self.panel_manager.add_panel(state)

            except Exception as e:
                self._show_error(f"Search error: {str(e)}")

    def _cmd_grep(self, args: List[str]):
        """Команда поиска в содержимом файлов"""
        if not args:
            return

        pattern = args[0]
        current_panel = self.panel_manager.get_current_panel()

        if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
            search_path = Path(current_panel.state.metadata['path'])

            try:
                results = []
                for root, dirs, files in os.walk(search_path):
                    for file in files:
                        file_path = Path(root) / file
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                for line_num, line in enumerate(f, 1):
                                    if pattern.lower() in line.lower():
                                        relative_path = file_path.relative_to(search_path)
                                        results.append(f"{relative_path}:{line_num}: {line.strip()}")

                        except (UnicodeDecodeError, PermissionError, OSError):
                            continue

                if results:
                    state = PanelState(
                        title=f"Grep: {pattern}",
                        content=results,
                        panel_type=PanelType.FILE
                    )
                    self.panel_manager.add_panel(state)
                else:
                    results = [f"Pattern '{pattern}' not found"]
                    state = PanelState(
                        title=f"Grep: {pattern}",
                        content=results,
                        panel_type=PanelType.FILE
                    )
                    self.panel_manager.add_panel(state)

            except Exception as e:
                self._show_error(f"Grep error: {str(e)}")

    def _cmd_tree(self, args: List[str]):
        """Команда показа дерева директорий"""
        current_panel = self.panel_manager.get_current_panel()
        if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
            path = Path(current_panel.state.metadata['path'])

            def build_tree(dir_path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
                if current_depth >= max_depth:
                    return []

                items = []
                try:
                    entries = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

                    for i, entry in enumerate(entries):
                        if entry.name.startswith('.') and not self.config['show_hidden']:
                            continue

                        is_last = i == len(entries) - 1
                        current_prefix = "└── " if is_last else "├── "
                        next_prefix = "    " if is_last else "│   "

                        icon = self._get_file_icon(entry, entry.is_dir())
                        items.append(f"{prefix}{current_prefix}{icon} {entry.name}")

                        if entry.is_dir():
                            items.extend(build_tree(entry, prefix + next_prefix, max_depth, current_depth + 1))

                except PermissionError:
                    items.append(f"{prefix}└── [Permission Denied]")

                return items

            tree_content = [f"📁 {path.name}"] + build_tree(path)

            state = PanelState(
                title=f"Tree: {path.name}",
                content=tree_content,
                panel_type=PanelType.FILE
            )
            self.panel_manager.add_panel(state)

    def _cmd_bookmark(self, args: List[str]):
        """Команда управления закладками"""
        if not args:
            # Показать все закладки
            if self.bookmarks:
                content = [f"{name}: {path}" for name, path in self.bookmarks.items()]
            else:
                content = ["No bookmarks saved"]

            state = PanelState(
                title="Bookmarks",
                content=content,
                panel_type=PanelType.FILE
            )
            self.panel_manager.add_panel(state)
            return

        action = args[0]
        if action == "add" and len(args) > 1:
            name = args[1]
            current_panel = self.panel_manager.get_current_panel()
            if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
                self.bookmarks[name] = current_panel.state.metadata['path']

        elif action == "go" and len(args) > 1:
            name = args[1]
            if name in self.bookmarks:
                self._open_directory(self.bookmarks[name])

        elif action == "remove" and len(args) > 1:
            name = args[1]
            if name in self.bookmarks:
                del self.bookmarks[name]

    def _cmd_history(self, args: List[str]):
        """Команда показа истории"""
        if self.history:
            content = [f"{i + 1}: {path}" for i, path in enumerate(self.history[-20:])]  # Последние 20
        else:
            content = ["No history available"]

        state = PanelState(
            title="History",
            content=content,
            panel_type=PanelType.FILE
        )
        self.panel_manager.add_panel(state)

    def _cmd_close(self, args: List[str]):
        """Команда закрытия панели"""
        self.panel_manager.remove_panel()
        self._setup_function_keys()

    def _cmd_branch(self, args: List[str]):
        """Команда управления ветками"""
        if not args:
            # Показать все ветки
            if self.panel_manager.branches:
                content = [f"{name}: {len(states)} panels" for name, states in self.panel_manager.branches.items()]
            else:
                content = ["No branches saved"]

            state = PanelState(
                title="Branches",
                content=content,
                panel_type=PanelType.FILE
            )
            self.panel_manager.add_panel(state)
            return

        action = args[0]
        if action == "save" and len(args) > 1:
            name = args[1]
            self.panel_manager.save_branch(name)
        elif action == "load" and len(args) > 1:
            name = args[1]
            self.panel_manager.load_branch(name)
            self._setup_function_keys()

    def _cmd_config(self, args: List[str]):
        """Команда настройки"""
        if not args:
            # Показать текущие настройки
            content = [f"{key}: {value}" for key, value in self.config.items()]
            state = PanelState(
                title="Configuration",
                content=content,
                panel_type=PanelType.FILE
            )
            self.panel_manager.add_panel(state)
            return

        if len(args) >= 2:
            key, value = args[0], args[1]
            if key in self.config:
                # Конвертируем тип значения
                if isinstance(self.config[key], bool):
                    value = value.lower() in ['true', '1', 'yes', 'on']
                elif isinstance(self.config[key], int):
                    try:
                        value = int(value)
                    except ValueError:
                        return

                self.config[key] = value
                self._save_config()

    def _cmd_help(self, args: List[str]):
        """Команда справки"""
        help_content = [
            "File Manager Commands:",
            "",
            "Navigation:",
            "  cd <path>        - Change directory",
            "  ls               - Refresh current directory",
            "  pwd              - Show current path",
            "",
            "Search:",
            "  find <pattern>   - Find files by name",
            "  grep <pattern>   - Search in file contents",
            "  tree             - Show directory tree",
            "",
            "Bookmarks:",
            "  bookmark         - Show all bookmarks",
            "  bookmark add <name> - Add current dir to bookmarks",
            "  bookmark go <name>  - Go to bookmark",
            "",
            "Panels:",
            "  close            - Close current panel",
            "  branch save <name> - Save current panel layout",
            "  branch load <name> - Load saved layout",
            "",
            "Keys:",
            "  Tab              - Switch between panels",
            "  Escape           - Close panel",
            "  Enter            - Open selected item",
            "  Arrow Keys       - Navigate",
            "  F1-F10           - Function keys (context dependent)",
            "",
            "Configuration:",
            "  config           - Show settings",
            "  config <key> <value> - Change setting"
        ]

        state = PanelState(
            title="Help",
            content=help_content,
            panel_type=PanelType.FILE
        )
        self.panel_manager.add_panel(state)

    def _cmd_quit(self, args: List[str]):
        """Команда выхода"""
        self._save_config()
        sys.exit(0)

    def handle_function_key(self, key: int):
        """Обработка функциональных клавиш"""
        current_panel = self.panel_manager.get_current_panel()
        if not current_panel:
            return

        # F1 - Help
        if key == curses.KEY_F1:
            self._cmd_help([])

        # F2 - Rename
        elif key == curses.KEY_F2:
            self._handle_rename()

        # F3 - View/Mode
        elif key == curses.KEY_F3:
            self._handle_view()

        # F4 - Edit/Extract
        elif key == curses.KEY_F4:
            self._handle_edit()

        # F5 - Copy/Extract All
        elif key == curses.KEY_F5:
            self._handle_copy()

        # F6 - Move/Add to Archive
        elif key == curses.KEY_F6:
            self._handle_move()

        # F7 - Mkdir/Search
        elif key == curses.KEY_F7:
            self._handle_mkdir_or_search()

        # F8 - Delete/Close
        elif key == curses.KEY_F8:
            self._handle_delete()

        # F10 - Quit
        elif key == curses.KEY_F10:
            self._cmd_quit([])

    def _handle_rename(self):
        """Обработка переименования"""
        # Упрощённая реализация - через командную строку
        self.panel_manager.command_line.text = "rename "

    def _handle_view(self):
        """Обработка просмотра"""
        current_panel = self.panel_manager.get_current_panel()
        if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
            selected = current_panel.get_selected_item()
            if selected:
                # Извлекаем имя файла из строки
                parts = selected.split()
                if len(parts) >= 2:
                    filename = parts[1]
                    current_path = Path(current_panel.state.metadata['path'])
                    file_path = current_path / filename
                    if file_path.exists():
                        self._open_file(file_path)

    def _handle_edit(self):
        """Обработка редактирования"""
        current_panel = self.panel_manager.get_current_panel()
        if current_panel:
            if current_panel.state.panel_type == PanelType.DIRECTORY:
                selected = current_panel.get_selected_item()
                if selected:
                    parts = selected.split()
                    if len(parts) >= 2:
                        filename = parts[1]
                        current_path = Path(current_panel.state.metadata['path'])
                        file_path = current_path / filename
                        if file_path.exists() and file_path.is_file():
                            # Открываем во внешнем редакторе
                            try:
                                subprocess.run([self.config['editor'], str(file_path)])
                            except Exception:
                                pass

    def _handle_copy(self):
        """Обработка копирования"""
        # Упрощённая реализация
        self.panel_manager.command_line.text = "copy "

    def _handle_move(self):
        """Обработка перемещения"""
        self.panel_manager.command_line.text = "move "

    def _handle_mkdir_or_search(self):
        """Обработка создания директории или поиска"""
        current_panel = self.panel_manager.get_current_panel()
        if current_panel:
            if current_panel.state.panel_type == PanelType.DIRECTORY:
                self.panel_manager.command_line.text = "mkdir "
            elif current_panel.state.panel_type == PanelType.FILE:
                self.panel_manager.command_line.text = "grep "

    def _handle_delete(self):
        """Обработка удаления"""
        current_panel = self.panel_manager.get_current_panel()
        if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
            self.panel_manager.command_line.text = "delete "
        else:
            # Закрыть панель
            self._cmd_close([])

    def run(self):
        """Основной цикл приложения"""
        try:
            # Первоначальная отрисовка
            self.panel_manager.draw()

            while True:
                # Получение нажатия клавиши
                key = self.stdscr.getch()

                # Обработка команд
                command = self.panel_manager.handle_key(key)
                if command:
                    self.panel_manager.execute_command(command)
                    self._setup_function_keys()  # Обновляем функциональные клавиши

                # Обработка функциональных клавиш
                if curses.KEY_F1 <= key <= curses.KEY_F12:
                    self.handle_function_key(key)
                    self._setup_function_keys()

                # Обработка Enter
                elif key == ord('\n') or key == ord('\r'):
                    current_panel = self.panel_manager.get_current_panel()
                    if current_panel and current_panel.state.panel_type == PanelType.DIRECTORY:
                        selected = current_panel.get_selected_item()
                        if selected and not selected.startswith("Error") and not selected.startswith("Permission"):
                            # Извлекаем имя файла
                            parts = selected.split()
                            if len(parts) >= 2:
                                filename = parts[1]
                                current_path = Path(current_panel.state.metadata['path'])
                                item_path = current_path / filename

                                if item_path.exists():
                                    if item_path.is_dir():
                                        self._open_directory(str(item_path))
                                    else:
                                        self._open_file(item_path)
                                    self._setup_function_keys()

                # Перерисовываем экран после каждого действия
                self.panel_manager.draw()

        except KeyboardInterrupt:
            self._cmd_quit([])


def main():
    """Главная функция"""

    def run_file_manager(stdscr):
        try:
            # Настройка curses
            curses.curs_set(1)  # Показать курсор
            stdscr.nodelay(False)
            stdscr.timeout(-1)
            stdscr.keypad(True)  # Включаем поддержку специальных клавиш

            # Очищаем экран перед началом
            stdscr.clear()
            stdscr.refresh()

            # Добавляем отладочное сообщение
            stdscr.addstr(0, 0, "Initializing File Manager...")
            stdscr.refresh()

            # Запуск файлового менеджера
            fm = FileManager(stdscr)
            fm.run()

        except Exception as e:
            # Восстанавливаем терминал перед показом ошибки
            curses.endwin()
            print(f"Error during execution: {e}")
            import traceback
            traceback.print_exc()

    try:
        curses.wrapper(run_file_manager)
    except Exception as e:
        print(f"Error initializing curses: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()