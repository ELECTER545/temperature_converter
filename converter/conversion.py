"""Формулы конвертации температур между шкалами C, F, K.
Все конвертации выполняются через каноническую шкалу — Цельсий.
Это даёт 3 формулы вместо 9: сначала из исходной шкалы
в Цельсий, затем из Цельсия в целевую. При этом функции чистые:
не читают ввод, не пишут в консоль, не знают про историю и файлы,
что делает их пригодными для юнит-тестов.
"""

from __future__ import annotations

from converter.scales import TemperatureScale

ABSOLUTE_ZERO_C: float = -273.15


def to_celsius(value: float, scale: TemperatureScale) -> float:
    """Перевести значение из заданной шкалы в градусы Цельсия.
    Args:
        value: числовое значение в исходной шкале.
        scale: исходная шкала температуры.
    Returns:
        Значение в градусах Цельсия.
    Raises:
        ValueError: если передана неподдерживаемая шкала.
    """
    if scale is TemperatureScale.CELSIUS:
        return value
    if scale is TemperatureScale.FAHRENHEIT:
        return (value - 32.0) * 5.0 / 9.0
    if scale is TemperatureScale.KELVIN:
        return value - 273.15
    raise ValueError(f"Неподдерживаемая шкала: {scale!r}")


def from_celsius(value_celsius: float, scale: TemperatureScale) -> float:
    """Перевести значение из градусов Цельсия в целевую шкалу.
    Args:
        value_celsius: значение в градусах Цельсия.
        scale: целевая шкала температуры.
    Returns:
        Значение в целевой шкале.
    Raises:
        ValueError: если передана неподдерживаемая шкала.
    """
    if scale is TemperatureScale.CELSIUS:
        return value_celsius
    if scale is TemperatureScale.FAHRENHEIT:
        return value_celsius * 9.0 / 5.0 + 32.0
    if scale is TemperatureScale.KELVIN:
        return value_celsius + 273.15
    raise ValueError(f"Неподдерживаемая шкала: {scale!r}")


def convert(
    value: float,
    from_scale: TemperatureScale,
    to_scale: TemperatureScale,
) -> float:
    """Сконвертировать значение из одной шкалы в другую.
    Args:
        value: исходное значение.
        from_scale: исходная шкала.
        to_scale: целевая шкала.
    Returns:
        Сконвертированное значение в целевой шкале.
    """
    return from_celsius(to_celsius(value, from_scale), to_scale)


def absolute_zero_in(scale: TemperatureScale) -> float:
    """Вернуть абсолютный ноль в заданной шкале.
    Используется в сообщениях об ошибке вида
    "минимум для этой шкалы: -459.67 F".
    Args:
        scale: шкала температуры.
    Returns:
        Значение абсолютного нуля в этой шкале.
    """
    return from_celsius(ABSOLUTE_ZERO_C, scale)