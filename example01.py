# example_handlers.py
"""
Пример обработчиков для демонстрационной конфигурации PanelFlow.
Эти классы должны быть переданы в handler_map при создании Application.
"""

from panelflow.core.handlers import BasePanelHandler
from typing import Any


class MainMenuHandler(BasePanelHandler):
    """Обработчик для главного меню."""

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        """
        Обработка действий в главном меню.

        Args:
            widget_id: ID виджета
            value: Значение виджета

        Returns:
            Команда навигации или None
        """
        if widget_id == "welcome_text":
            print("Добро пожаловать в PanelFlow!")
            return None

        # Для PanelLink навигация происходит автоматически
        return None


class SettingsHandler(BasePanelHandler):
    """Обработчик для панели настроек."""

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        """
        Обработка изменений настроек.

        Args:
            widget_id: ID виджета
            value: Значение виджета

        Returns:
            Команда навигации или None
        """
        if widget_id == "theme_select":
            print(f"Тема изменена на: {value}")
            # Можно добавить логику применения темы
            return None

        elif widget_id == "save_settings":
            print("Настройки сохранены:")
            print(f"- Тема: {self.form_data.get('theme_select', 'Светлая')}")
            print(f"- Язык: {self.form_data.get('language_select', 'Русский')}")
            return None

        return None


class UserFormHandler(BasePanelHandler):
    """Обработчик для формы пользователя."""

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        """
        Обработка формы пользователя.

        Args:
            widget_id: ID виджета
            value: Значение виджета

        Returns:
            Команда навигации или None
        """
        if widget_id == "user_name":
            # Валидация имени пользователя
            if len(value) < 2:
                print("Имя пользователя должно содержать минимум 2 символа")
            return None

        elif widget_id == "submit_form":
            # Валидация и отправка формы
            name = self.form_data.get('user_name', '')
            email = self.form_data.get('user_email', '')
            role = self.form_data.get('user_role', 'Пользователь')

            if not name:
                print("Ошибка: Имя пользователя обязательно")
                return None

            if not email:
                print("Ошибка: Email обязателен")
                return None

            print("Форма успешно отправлена:")
            print(f"- Имя: {name}")
            print(f"- Email: {email}")
            print(f"- Роль: {role}")

            # Навигация к профилю после успешной отправки
            return ("navigate_down", "user_profile")

        return None


class ProfileHandler(BasePanelHandler):
    """Обработчик для профиля пользователя."""

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        """
        Обработка действий в профиле.

        Args:
            widget_id: ID виджета
            value: Значение виджета

        Returns:
            Команда навигации или None
        """
        if widget_id == "profile_info":
            # Показать информацию из контекста
            print("Информация профиля:")
            print(f"- Имя: {self.context.get('user_name', 'Не указано')}")
            print(f"- Email: {self.context.get('user_email', 'Не указано')}")
            print(f"- Роль: {self.context.get('user_role', 'Пользователь')}")
            return None

        return None


# Словарь обработчиков для передачи в Application
HANDLER_MAP = {
    "MainMenuHandler": MainMenuHandler,
    "SettingsHandler": SettingsHandler,
    "UserFormHandler": UserFormHandler,
    "ProfileHandler": ProfileHandler
}

# Пример использования
if __name__ == "__main__":
    from panelflow.core import Application

    # Создание приложения
    app = Application(
        config_path="application.json",
        handler_map=HANDLER_MAP
    )

    print("Приложение PanelFlow успешно инициализировано!")
    print(f"Панель входа: {app._entry_panel_id}")
    print(f"Всего панелей: {len(app._panel_templates)}")
    print(f"Активная панель: {app.active_node.panel_template.title}")