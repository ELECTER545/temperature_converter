"""Тесты для модуля converter.history.

Каждый тест работает в своём временном каталоге (tempfile.TemporaryDirectory),
поэтому тесты не мешают друг другу и не засоряют рабочую папку проекта.

Покрываем не только happy path, но и «шаловливые руки» пользователя:
стёртое содержимое файла, удалённый заголовок, битые строки.
"""

import tempfile
import unittest
from pathlib import Path

from converter.history import (
    VALUE_DECIMALS,
    HistoryRecord,
    HistoryStorage,
)
from converter.scales import TemperatureScale


class HistoryStorageTests(unittest.TestCase):
    """Тесты записи и чтения истории через HistoryStorage."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / "history.csv"
        self._storage = HistoryStorage(self._path)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # --- Чтение ---------------------------------------------------

    def test_read_missing_file_returns_empty(self) -> None:
        self.assertFalse(self._path.exists())
        self.assertEqual(self._storage.read_all(), [])

    def test_read_empty_file_returns_empty(self) -> None:
        self._path.write_text("", encoding="utf-8")
        self.assertEqual(self._storage.read_all(), [])

    # --- Запись ---------------------------------------------------

    def test_append_creates_file(self) -> None:
        self.assertFalse(self._path.exists())
        self._storage.append(
            TemperatureScale.CELSIUS, 0.0,
            TemperatureScale.FAHRENHEIT, 32.0,
        )
        self.assertTrue(self._path.exists())

    def test_append_returns_record(self) -> None:
        record = self._storage.append(
            TemperatureScale.CELSIUS, 36.6,
            TemperatureScale.FAHRENHEIT, 97.88,
        )
        self.assertIsInstance(record, HistoryRecord)
        self.assertEqual(record.from_scale, TemperatureScale.CELSIUS)
        self.assertEqual(record.from_value, 36.6)
        self.assertEqual(record.to_scale, TemperatureScale.FAHRENHEIT)
        self.assertEqual(record.to_value, 97.88)

    def test_append_then_read(self) -> None:
        self._storage.append(
            TemperatureScale.CELSIUS, 0.0,
            TemperatureScale.FAHRENHEIT, 32.0,
        )
        self._storage.append(
            TemperatureScale.KELVIN, 300.0,
            TemperatureScale.CELSIUS, 26.85,
        )
        records = self._storage.read_all()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].from_scale, TemperatureScale.CELSIUS)
        self.assertEqual(records[1].from_scale, TemperatureScale.KELVIN)

    # --- Формат файла --------------------------------------------

    def test_csv_header_written_once(self) -> None:
        self._storage.append(
            TemperatureScale.CELSIUS, 0.0,
            TemperatureScale.FAHRENHEIT, 32.0,
        )
        self._storage.append(
            TemperatureScale.CELSIUS, 100.0,
            TemperatureScale.FAHRENHEIT, 212.0,
        )
        lines = self._path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 3)  # заголовок + 2 записи
        self.assertEqual(
            lines[0], "timestamp,from_scale,from_value,to_scale,to_value"
        )

    def test_values_formatted_with_two_decimals(self) -> None:
        self._storage.append(
            TemperatureScale.CELSIUS, 36.6,
            TemperatureScale.FAHRENHEIT, 97.88,
        )
        content = self._path.read_text(encoding="utf-8")
        self.assertIn(",C,36.60,F,97.88", content)

    def test_value_decimals_constant(self) -> None:
        self.assertEqual(VALUE_DECIMALS, 2)

    # --- Устойчивость к «шаловливым рукам» -----------------------

    def test_wiped_file_gets_header_again(self) -> None:
        # Пользователь стёр содержимое: файл существует, но пуст.
        self._storage.append(
            TemperatureScale.CELSIUS, 0.0,
            TemperatureScale.FAHRENHEIT, 32.0,
        )
        self._path.write_text("", encoding="utf-8")

        self._storage.append(
            TemperatureScale.KELVIN, 300.0,
            TemperatureScale.CELSIUS, 26.85,
        )
        content = self._path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("timestamp,"))

    def test_missing_header_first_row_not_lost(self) -> None:
        # Пользователь удалил только заголовок, данные остались.
        self._storage.append(
            TemperatureScale.CELSIUS, 0.0,
            TemperatureScale.FAHRENHEIT, 32.0,
        )
        self._storage.append(
            TemperatureScale.KELVIN, 300.0,
            TemperatureScale.CELSIUS, 26.85,
        )
        lines = self._path.read_text(encoding="utf-8").splitlines()
        self._path.write_text(
            "\n".join(lines[1:]) + "\n", encoding="utf-8"
        )

        records = self._storage.read_all()
        self.assertEqual(len(records), 2)  # первая запись не съедена

    def test_corrupted_row_skipped(self) -> None:
        # Одна строка битая — остальные должны прочитаться.
        self._path.write_text(
            "timestamp,from_scale,from_value,to_scale,to_value\n"
            "2026-11-08 10:00:00,C,0.00,F,32.00\n"
            "мусор,без,правильного,формата,здесь\n"
            "2026-11-08 10:01:00,K,300.00,C,26.85\n",
            encoding="utf-8",
        )
        records = self._storage.read_all()
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()