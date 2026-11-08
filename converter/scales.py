"""Шкалы измерения температуры."""

from __future__ import annotations

from enum import Enum


class TemperatureScale(Enum):
    """Перечисление поддерживаемых шкал температуры.
    Значение (value) — короткий код латиницей (C / F / K).
    Он используется в CSV-файле истории, чтобы файл был компактным
    и однозначно читался. Человекочитаемые названия — в свойстве
    full_name; они используются в консольном интерфейсе.
    """

    CELSIUS = "C"
    FAHRENHEIT = "F"
    KELVIN = "K"

    @property
    def short_name(self) -> str:
        """Короткий код шкалы (C / F / K)."""
        return self.value

    @property
    def full_name(self) -> str:
        """Человекочитаемое название шкалы для меню и сообщений."""
        return {
            TemperatureScale.CELSIUS: "Цельсий",
            TemperatureScale.FAHRENHEIT: "Фаренгейт",
            TemperatureScale.KELVIN: "Кельвин",
        }[self]

    def __str__(self) -> str:
        """Формат для печати в консоль: 'Цельсий (C)'."""
        return f"{self.full_name} ({self.short_name})"

    @classmethod
    def from_code(cls, code: str) -> "TemperatureScale":
        """Получить шкалу по короткому коду (без учёта регистра).
        Args:
            code: код шкалы, например "C", "f" или "K".
        Returns:
            Соответствующий элемент TemperatureScale.
        Raises:
            ValueError: если код не соответствует ни одной шкале.
        """
        normalized = code.strip().upper()
        for scale in cls:
            if scale.value == normalized:
                return scale
        raise ValueError(f"Неизвестная шкала: {code!r}")