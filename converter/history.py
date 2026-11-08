"""Сохранение и чтение истории конвертаций в CSV-файл.

История — текстовый CSV с заголовком и одной строкой на конвертацию:

    timestamp,from_scale,from_value,to_scale,to_value
    2026-11-08 14:30:12,C,36.60,F,97.88

Формат выбран потому, что CSV:
  * текстовый (соответствует ТЗ),
  * открывается в Excel и в блокноте,
  * стандартная библиотека `csv` умеет и писать, и читать без зависимостей.

Модуль не печатает в консоль — вся коммуникация с пользователем
остаётся в CLI-слое. Ошибки ввода-вывода оборачиваются в HistoryError.
"""

from __future__ import annotations

import csv
import itertools
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from converter.exceptions import HistoryError
from converter.scales import TemperatureScale

# Имена колонок CSV вынесены в константы — так их не надо помнить
# наизусть и невозможно опечататься в двух местах (DRY).
_CSV_HEADER: tuple[str, ...] = (
    "timestamp",
    "from_scale",
    "from_value",
    "to_scale",
    "to_value",
)

# Количество знаков после запятой при сохранении значений.
# То же значение используется в CLI при выводе — так пользователь
# видит в консоли ровно то, что потом найдёт в файле истории.
VALUE_DECIMALS: int = 2


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    """Одна запись истории конвертации.

    Атрибуты:
        timestamp: момент конвертации (локальное время).
        from_scale: исходная шкала.
        from_value: исходное значение в исходной шкале.
        to_scale: целевая шкала.
        to_value: результат в целевой шкале.
    """

    timestamp: datetime
    from_scale: TemperatureScale
    from_value: float
    to_scale: TemperatureScale
    to_value: float


class HistoryStorage:
    """Хранилище истории конвертаций в CSV-файле.

    Класс инкапсулирует путь к файлу и формат CSV. Путь передаётся
    в конструкторе — это позволяет легко подменить его в тестах
    на временный файл и не привязываться к рабочему каталогу.

    Args:
        path: путь к CSV-файлу истории. Файл может не существовать —
            он будет создан при первом добавлении записи.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        """Путь к файлу истории (только для чтения)."""
        return self._path

    def append(
        self,
        from_scale: TemperatureScale,
        from_value: float,
        to_scale: TemperatureScale,
        to_value: float,
    ) -> HistoryRecord:
        """Добавить одну запись в конец файла истории.

        Если файл не существует или пуст — создаёт его и пишет заголовок.
        Если существует и непуст — дописывает строку, не перезаписывая
        старые.

        Args:
            from_scale: исходная шкала.
            from_value: исходное значение.
            to_scale: целевая шкала.
            to_value: результат конвертации.

        Returns:
            Созданная запись (с проставленным временем).

        Raises:
            HistoryError: если файл нельзя открыть/записать или
                запись не сериализуется в CSV.
        """
        record = HistoryRecord(
            timestamp=datetime.now(),
            from_scale=from_scale,
            from_value=from_value,
            to_scale=to_scale,
            to_value=to_value,
        )

        try:
            # newline="" — требование модуля csv, иначе на Windows
            # между строками появятся пустые строки из-за \r\n.
            # encoding="utf-8" — чтобы русские сообщения и любые
            # не-ASCII символы читались корректно на любой локали.
            # Заголовок нужен, если файла нет ИЛИ он пуст (пользователь
            # мог стереть содержимое вручную — тогда is_fresh должен
            # сработать, как и при первом запуске).
            is_fresh = (
                not self._path.exists()
                or self._path.stat().st_size == 0
            )
            with self._path.open("a", encoding="utf-8", newline="") as fh:
                writer = csv.writer(fh, delimiter=",")
                if is_fresh:
                    writer.writerow(_CSV_HEADER)
                writer.writerow(
                    (
                        record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        record.from_scale.short_name,
                        f"{record.from_value:.{VALUE_DECIMALS}f}",
                        record.to_scale.short_name,
                        f"{record.to_value:.{VALUE_DECIMALS}f}",
                    )
                )
        except OSError as exc:
            # Все ошибки файловой системы (нет прав, диск занят, путь
            # указывает на каталог и т.п.) приводим к одному типу.
            raise HistoryError(
                f"Не удалось записать историю в {self._path}: {exc}"
            ) from exc

        return record

    def read_all(self) -> list[HistoryRecord]:
        """Прочитать все записи из файла истории.

        Если файла нет или он пуст — возвращает пустой список
        (это нормальная ситуация: пользователь ещё ничего не
        конвертировал).
        Если в файле нет заголовка (например, пользователь удалил
        первую строку) — первая строка пытается разобраться как
        запись, а не теряется.
        Битые строки пропускаются, чтобы одна повреждённая запись
        не блокировала просмотр всей истории.

        Returns:
            Список записей в порядке добавления (старые сверху).

        Raises:
            HistoryError: если файл существует, но не читается
                (нет прав, это каталог и т.п.).
        """
        if not self._path.exists():
            return []

        records: list[HistoryRecord] = []
        try:
            with self._path.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.reader(fh, delimiter=",")
                first_row = next(reader, None)
                if first_row is None:
                    return []

                # Строка считается заголовком только если она действительно
                # похожа на заголовок. Если пользователь удалил заголовок
                # (или файл из другого источника), первая строка может быть
                # данными — в этом случае не теряем её, пытаемся разобрать.
                if tuple(first_row) == _CSV_HEADER:
                    data_rows = reader
                else:
                    # itertools.chain позволяет обработать первую строку
                    # как данные и продолжить итерацию по остатку файла.
                    data_rows = itertools.chain([first_row], reader)

                for row in data_rows:
                    record = _row_to_record(row)
                    if record is not None:
                        records.append(record)
        except OSError as exc:
            raise HistoryError(
                f"Не удалось прочитать историю из {self._path}: {exc}"
            ) from exc

        return records


def _row_to_record(row: list[str]) -> HistoryRecord | None:
    """Преобразовать строку CSV в HistoryRecord.

    Служебная функция модуля. Возвращает None, если строку нельзя
    разобрать (битая запись), — вызывающий код такие строки пропускает.

    Args:
        row: список полей одной строки CSV.

    Returns:
        HistoryRecord при успехе, None при любой ошибке разбора.
    """
    if len(row) != len(_CSV_HEADER):
        return None
    try:
        return HistoryRecord(
            timestamp=datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"),
            from_scale=TemperatureScale.from_code(row[1]),
            from_value=float(row[2]),
            to_scale=TemperatureScale.from_code(row[3]),
            to_value=float(row[4]),
        )
    except (ValueError, TypeError):
        return None