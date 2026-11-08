"""Точка входа конвертера температур.

Собирает зависимости и запускает консольный интерфейс. Вся логика —
в пакете converter; здесь только «проводка» (composition root).

Запуск:
    python main.py
"""

from __future__ import annotations

from pathlib import Path

from converter.cli import ConsoleApp
from converter.history import HistoryStorage


def _history_path() -> Path:
    """Вернуть путь к файлу истории рядом с main.py.

    Используется Path(__file__).resolve().parent, а не относительный
    путь "history.csv": тогда файл создаётся рядом с программой,
    независимо от текущего рабочего каталога запуска.

    Returns:
        Абсолютный путь к history.csv в каталоге проекта.
    """
    return Path(__file__).resolve().parent / "history.csv"


def main() -> None:
    """Собрать приложение и запустить главный цикл."""
    storage = HistoryStorage(_history_path())
    ConsoleApp(storage).run()


if __name__ == "__main__":
    main()