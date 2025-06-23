from blessed import Terminal
import time


def main():
    term = Terminal()

    with term.fullscreen(), term.cbreak():
        # Отступы
        top_offset = 3
        left_offset = 3

        # Размеры панелей
        panel_width = (term.width - left_offset * 2) // 3
        panel_height = term.height - top_offset - 3

        print(term.clear)

        # Рисуем панели
        for i in range(3):
            x = left_offset + i * panel_width
            # Верхняя линия
            print(term.move_yx(top_offset, x) + "┌" + "─" * (panel_width - 2) + "┐")
            # Боковые линии
            for y in range(1, panel_height - 1):
                print(term.move_yx(top_offset + y, x) + "│")
                print(term.move_yx(top_offset + y, x + panel_width - 1) + "│")
            # Нижняя линия
            print(term.move_yx(top_offset + panel_height - 1, x) + "└" + "─" * (panel_width - 2) + "┘")
            # Заголовок
            print(term.move_yx(top_offset + 1, x + 2) + f"Панель {i + 1}")

        # Поле ввода
        input_y = term.height - 3
        print(term.move_yx(input_y, left_offset) + "Ввод: ")

        time.sleep(5)  # Показываем интерфейс на 5 секунд


if __name__ == "__main__":
    main()