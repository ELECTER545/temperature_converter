"""Тесты для модуля converter.validators.

Проверяем парсинг чисел (точка/запятая), отказ от NaN/inf, проверку
абсолютного нуля для всех трёх шкал и разбор пунктов меню.
"""

import unittest

from converter.exceptions import (
    BelowAbsoluteZeroError,
    InvalidInputError,
)
from converter.scales import TemperatureScale
from converter.validators import (
    parse_menu_choice,
    parse_temperature,
    validate_above_absolute_zero,
)


class ParseTemperatureTests(unittest.TestCase):
    """Тесты parse_temperature: строки -> float."""

    def test_dot_decimal(self) -> None:
        self.assertEqual(parse_temperature("36.6"), 36.6)

    def test_comma_decimal(self) -> None:
        self.assertEqual(parse_temperature("36,6"), 36.6)

    def test_integer(self) -> None:
        self.assertEqual(parse_temperature("42"), 42.0)

    def test_negative(self) -> None:
        self.assertEqual(parse_temperature("-10.5"), -10.5)

    def test_surrounding_whitespace(self) -> None:
        self.assertEqual(parse_temperature("  25.5  "), 25.5)

    def test_empty_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_temperature("")

    def test_whitespace_only_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_temperature("   ")

    def test_letters_raise(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_temperature("abc")

    def test_nan_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_temperature("nan")

    def test_inf_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_temperature("inf")


class ValidateAboveAbsoluteZeroTests(unittest.TestCase):
    """Тесты validate_above_absolute_zero для всех шкал."""

    def test_celsius_exact_zero_ok(self) -> None:
        # -273.15 C — ровно абсолютный ноль, должен приниматься.
        validate_above_absolute_zero(-273.15, TemperatureScale.CELSIUS)

    def test_celsius_below_zero_raises(self) -> None:
        with self.assertRaises(BelowAbsoluteZeroError):
            validate_above_absolute_zero(-273.16, TemperatureScale.CELSIUS)

    def test_kelvin_exact_zero_ok(self) -> None:
        validate_above_absolute_zero(0.0, TemperatureScale.KELVIN)

    def test_kelvin_below_zero_raises(self) -> None:
        with self.assertRaises(BelowAbsoluteZeroError):
            validate_above_absolute_zero(-0.01, TemperatureScale.KELVIN)

    def test_fahrenheit_exact_zero_ok_epsilon(self) -> None:
        # Ключевой кейс: -459.67 F в float-арифметике даёт чуть меньше
        # -273.15 C. Без epsilon этот корректный ввод отклонялся бы.
        validate_above_absolute_zero(-459.67, TemperatureScale.FAHRENHEIT)

    def test_fahrenheit_below_zero_raises(self) -> None:
        with self.assertRaises(BelowAbsoluteZeroError):
            validate_above_absolute_zero(-459.68, TemperatureScale.FAHRENHEIT)

    def test_error_message_uses_input_units(self) -> None:
        # Сообщение должно быть в единицах ввода, а не в Цельсиях.
        with self.assertRaises(BelowAbsoluteZeroError) as ctx:
            validate_above_absolute_zero(-1.0, TemperatureScale.KELVIN)
        self.assertIn("K", str(ctx.exception))
        self.assertIn("0.00", str(ctx.exception))


class ParseMenuChoiceTests(unittest.TestCase):
    """Тесты parse_menu_choice: строка -> номер пункта."""

    def test_valid_choice(self) -> None:
        self.assertEqual(parse_menu_choice("2", range(1, 4)), 2)

    def test_first_choice(self) -> None:
        self.assertEqual(parse_menu_choice("1", range(1, 4)), 1)

    def test_last_choice(self) -> None:
        self.assertEqual(parse_menu_choice("3", range(1, 4)), 3)

    def test_with_whitespace(self) -> None:
        self.assertEqual(parse_menu_choice("  2  ", range(1, 4)), 2)

    def test_empty_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_menu_choice("", range(1, 4))

    def test_not_integer_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_menu_choice("abc", range(1, 4))

    def test_float_string_raises(self) -> None:
        # int("2.5") бросает ValueError — это тоже InvalidInputError.
        with self.assertRaises(InvalidInputError):
            parse_menu_choice("2.5", range(1, 4))

    def test_out_of_range_high_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_menu_choice("5", range(1, 4))

    def test_out_of_range_low_raises(self) -> None:
        with self.assertRaises(InvalidInputError):
            parse_menu_choice("0", range(1, 4))


if __name__ == "__main__":
    unittest.main()