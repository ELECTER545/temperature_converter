"""Консольный интерфейс конвертера температур.
Модуль отвечает только за диалог с пользователем: меню, ввод значений,
вывод результата и истории, показ понятных сообщений об ошибках.
Формулы, валидация и работа с файлом истории вынесены в отдельные
модули — это делает CLI тонким и упрощает его замену на GUI/бота.
"""

from __future__ import annotations

from converter.conversion import convert
from converter.exceptions import ConverterError
from converter.history import VALUE_DECIMALS, HistoryRecord, HistoryStorage
from converter.scales import TemperatureScale
from converter.validators import (
    parse_menu_choice,
    parse_temperature,
    validate_above_absolute_zero,
)

# Допустимые номера пунктов меню. range(1, 4) == 1, 2, 3.
_MAIN_MENU_CHOICES = range(1, 4)
_SCALE_MENU_CHOICES = range(1, 4)

# Порядок шкал в меню. tuple(Enum) возвращает элементы в порядке объявления
# в scales.py: CELSIUS, FAHRENHEIT, KELVIN.
_SCALE_LIST: tuple[TemperatureScale, ...] = tuple(TemperatureScale)


class _ExitRequested(Exception):
    """Служебное исключение: пользователь нажал Ctrl+C или Ctrl+D."""


class ConsoleApp:
    """Консольное приложение конвертера температур.

    Args:
        history: хранилище истории конвертаций (инъекция зависимости —
            в тестах можно подменить на временный файл).
    """

    def __init__(self, history: HistoryStorage) -> None:
        self._history = history
        self._running = True

    def run(self) -> None:
        """Запустить главный цикл приложения.

        Завершается по выбору пункта «Выход» или по Ctrl+C / Ctrl+D.
        """
        self._print_header()
        try:
            while self._running:
                self._print_main_menu()
                try:
                    choice = parse_menu_choice(
                        self._safe_input("> "), _MAIN_MENU_CHOICES
                    )
                except ConverterError as err:
                    # Неверный пункт меню — сообщаем и крутимся дальше.
                    print(f"Ошибка: {err}")
                    continue

                if choice == 1:
                    self._handle_convert()
                elif choice == 2:
                    self._handle_show_history()
                elif choice == 3:
                    self._running = False
        except _ExitRequested:
            # Ctrl+C / Ctrl+D — выходим без traceback.
            print()
        print("До свидания.")

    # ------------------------------------------------------------------
    # Ввод-вывод
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_input(prompt: str) -> str:
        """input(), превращающий Ctrl+C / Ctrl+D в аккуратный выход.

        Args:
            prompt: текст приглашения.

        Returns:
            Введённая строка.

        Raises:
            _ExitRequested: если пользователь прервал ввод.
        """
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            raise _ExitRequested from None

    def _print_header(self) -> None:
        """Напечатать шапку приложения."""
        print("=" * 50)
        print("  Конвертер температур (C / F / K)")
        print("=" * 50)

    def _print_main_menu(self) -> None:
        """Напечатать главное меню."""
        print()
        print("Главное меню:")
        print("  1. Конвертировать температуру")
        print("  2. Показать историю")
        print("  3. Выход")

    # ------------------------------------------------------------------
    # Сценарий 1: конвертация
    # ------------------------------------------------------------------

    def _handle_convert(self) -> None:
        """Провести пользователя по сценарию конвертации."""
        from_scale = self._choose_scale("Исходная шкала")
        to_scale = self._choose_scale("Целевая шкала")
        
        # Если шкалы совпадают, конвертация тривиальна — предупреждаем
        # и спрашиваем подтверждение. Пользователь может случайно выбрать
        # одну и ту же шкалу в обоих меню.
        if from_scale is to_scale:
            print()
            print(
                f"Внимание: исходная и целевая шкалы совпадают "
                f"({from_scale}). Результат будет равен введённому значению."
            )
            answer = self._safe_input("Продолжить? (y/n): ").strip().lower()
            if answer not in ("y", "yes", "д", "да"):
                print("Отменено.")
                return

        value = self._prompt_temperature(from_scale)

        try:
            validate_above_absolute_zero(value, from_scale)
        except ConverterError as err:
            print(f"Ошибка: {err}")
            return

        result = convert(value, from_scale, to_scale)

        print()
        print(
            f"{value:.{VALUE_DECIMALS}f} {from_scale.short_name} = "
            f"{result:.{VALUE_DECIMALS}f} {to_scale.short_name}"
        )

        try:
            self._history.append(from_scale, value, to_scale, result)
            print("Запись сохранена в историю.")
        except ConverterError as err:
            # Конвертация удалась, но запись не сохранилась — сообщаем
            # об этом отдельно, не прерывая работу программы.
            print(f"Не удалось сохранить в историю: {err}")

    def _choose_scale(self, title: str) -> TemperatureScale:
        """Запросить шкалу через нумерованное меню.
        Повторяет запрос, пока пользователь не введёт корректный номер.
        Args:
            title: заголовок меню («Исходная шкала» / «Целевая шкала»).
        Returns:
            Выбранная шкала.
        """
        while True:
            print()
            print(f"{title}:")
            for index, scale in enumerate(_SCALE_LIST, start=1):
                print(f"  {index}. {scale}")
            try:
                choice = parse_menu_choice(
                    self._safe_input("> "), _SCALE_MENU_CHOICES
                )
            except ConverterError as err:
                print(f"Ошибка: {err}")
                continue
            return _SCALE_LIST[choice - 1]

    def _prompt_temperature(self, scale: TemperatureScale) -> float:
        """Запросить значение температуры, пока ввод не станет корректным.
        Args:
            scale: шкала, в которой вводится значение (для приглашения).
        Returns:
            Числовое значение.
        """
        while True:
            try:
                return parse_temperature(
                    self._safe_input(f"Введите значение в шкале {scale}: ")
                )
            except ConverterError as err:
                print(f"Ошибка: {err}")
                continue

    # ------------------------------------------------------------------
    # Сценарий 2: история
    # ------------------------------------------------------------------

    def _handle_show_history(self) -> None:
        """Показать все записи истории (или сообщить, что она пуста)."""
        try:
            records = self._history.read_all()
        except ConverterError as err:
            print(f"Ошибка: {err}")
            return

        if not records:
            print()
            print("История пуста.")
            return

        print()
        print(f"История ({len(records)} записей):")
        print("-" * 60)
        for record in records:
            self._print_record(record)
        print("-" * 60)

    @staticmethod
    def _print_record(record: HistoryRecord) -> None:
        """Напечатать одну запись истории в формате "дата  36.60 C = 97.88 F".
        Args:
            record: запись истории.
        """
        timestamp = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"{timestamp}  "
            f"{record.from_value:.{VALUE_DECIMALS}f} {record.from_scale.short_name} = "
            f"{record.to_value:.{VALUE_DECIMALS}f} {record.to_scale.short_name}"
        )