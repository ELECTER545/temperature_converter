"""Тесты для модуля converter.conversion.

Проверяем формулы и обратимость конвертаций. Для float-сравнений
используем assertAlmostEqual с places=7 — этого достаточно, чтобы
учесть погрешности IEEE 754 и не ловить ложные падения.
"""

import unittest

from converter.conversion import (
    ABSOLUTE_ZERO_C,
    absolute_zero_in,
    convert,
    from_celsius,
    to_celsius,
)
from converter.scales import TemperatureScale


class ToCelsiusTests(unittest.TestCase):
    """Тесты to_celsius: перевод из исходной шкалы в Цельсий."""

    def test_celsius_passthrough(self) -> None:
        self.assertEqual(to_celsius(25.0, TemperatureScale.CELSIUS), 25.0)

    def test_fahrenheit_freezing(self) -> None:
        self.assertAlmostEqual(
            to_celsius(32.0, TemperatureScale.FAHRENHEIT), 0.0
        )

    def test_fahrenheit_boiling(self) -> None:
        self.assertAlmostEqual(
            to_celsius(212.0, TemperatureScale.FAHRENHEIT), 100.0
        )

    def test_fahrenheit_absolute_zero(self) -> None:
        self.assertAlmostEqual(
            to_celsius(-459.67, TemperatureScale.FAHRENHEIT), -273.15
        )

    def test_kelvin_freezing(self) -> None:
        self.assertAlmostEqual(
            to_celsius(273.15, TemperatureScale.KELVIN), 0.0
        )

    def test_kelvin_absolute_zero(self) -> None:
        self.assertAlmostEqual(
            to_celsius(0.0, TemperatureScale.KELVIN), -273.15
        )


class FromCelsiusTests(unittest.TestCase):
    """Тесты from_celsius: перевод из Цельсия в целевую шкалу."""

    def test_celsius_passthrough(self) -> None:
        self.assertEqual(
            from_celsius(25.0, TemperatureScale.CELSIUS), 25.0
        )

    def test_fahrenheit_freezing(self) -> None:
        self.assertAlmostEqual(
            from_celsius(0.0, TemperatureScale.FAHRENHEIT), 32.0
        )

    def test_fahrenheit_boiling(self) -> None:
        self.assertAlmostEqual(
            from_celsius(100.0, TemperatureScale.FAHRENHEIT), 212.0
        )

    def test_kelvin_freezing(self) -> None:
        self.assertAlmostEqual(
            from_celsius(0.0, TemperatureScale.KELVIN), 273.15
        )

    def test_kelvin_absolute_zero(self) -> None:
        self.assertAlmostEqual(
            from_celsius(-273.15, TemperatureScale.KELVIN), 0.0
        )


class ConvertTests(unittest.TestCase):
    """Тесты convert: конвертация из любой шкалы в любую."""

    def test_same_scale_returns_same_value(self) -> None:
        # C -> C, F -> F, K -> K возвращают вход без искажений.
        for scale in TemperatureScale:
            with self.subTest(scale=scale):
                self.assertAlmostEqual(
                    convert(42.5, scale, scale), 42.5, places=7
                )

    def test_celsius_to_fahrenheit(self) -> None:
        self.assertAlmostEqual(
            convert(36.6, TemperatureScale.CELSIUS,
                    TemperatureScale.FAHRENHEIT),
            97.88, places=2,
        )

    def test_fahrenheit_to_celsius(self) -> None:
        self.assertAlmostEqual(
            convert(98.6, TemperatureScale.FAHRENHEIT,
                    TemperatureScale.CELSIUS),
            37.0, places=2,
        )

    def test_celsius_to_kelvin(self) -> None:
        self.assertAlmostEqual(
            convert(0.0, TemperatureScale.CELSIUS,
                    TemperatureScale.KELVIN),
            273.15, places=7,
        )

    def test_kelvin_to_celsius(self) -> None:
        self.assertAlmostEqual(
            convert(300.0, TemperatureScale.KELVIN,
                    TemperatureScale.CELSIUS),
            26.85, places=2,
        )

    def test_round_trip_c_f_c(self) -> None:
        # C -> F -> C должен вернуть исходное значение (с точностью float).
        value = 42.0
        round_trip = convert(
            convert(value, TemperatureScale.CELSIUS,
                    TemperatureScale.FAHRENHEIT),
            TemperatureScale.FAHRENHEIT,
            TemperatureScale.CELSIUS,
        )
        self.assertAlmostEqual(round_trip, value, places=7)

    def test_round_trip_k_c_k(self) -> None:
        value = 300.0
        round_trip = convert(
            convert(value, TemperatureScale.KELVIN,
                    TemperatureScale.CELSIUS),
            TemperatureScale.CELSIUS,
            TemperatureScale.KELVIN,
        )
        self.assertAlmostEqual(round_trip, value, places=7)


class AbsoluteZeroTests(unittest.TestCase):
    """Тесты absolute_zero_in: абсолютный ноль в каждой шкале."""

    def test_celsius(self) -> None:
        self.assertAlmostEqual(
            absolute_zero_in(TemperatureScale.CELSIUS), -273.15
        )

    def test_kelvin(self) -> None:
        self.assertAlmostEqual(
            absolute_zero_in(TemperatureScale.KELVIN), 0.0
        )

    def test_fahrenheit(self) -> None:
        self.assertAlmostEqual(
            absolute_zero_in(TemperatureScale.FAHRENHEIT), -459.67
        )

    def test_constant(self) -> None:
        self.assertEqual(ABSOLUTE_ZERO_C, -273.15)


if __name__ == "__main__":
    unittest.main()