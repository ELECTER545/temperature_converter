"""Валидация пользовательского ввода.
Модуль отвечает за преобразование строк в числа, проверку физических
ограничений (абсолютный ноль) и разбор номеров пунктов меню. Ничего
не печатает — вся коммуникация с пользователем остаётся в CLI-слое.
"""

from __future__ import annotations

import math

from converter.conversion import ABSOLUTE_ZERO_C, absolute_zero_in, to_celsius
from converter.exceptions import BelowAbsoluteZeroError, InvalidInputError
from converter.scales import TemperatureScale


_ABSOLUTE_ZERO_EPSILON: float = 1e-9


def parse_temperature(raw: str) -> float:
    """Преобразовать строку в число с плавающей точкой.
    Принимает и точку, и запятую в качестве десятичного разделителя
    ("25.5" и "25,5" эквивалентны). Отклоняет пустые строки,
    бесконечности и NaN.
    Args:
        raw: строка, введённая пользователем.
    Returns:
        Число с плавающей точкой.
    Raises:
        InvalidInputError: если строку нельзя интерпретировать как число,
            либо если полученное значение — NaN или бесконечность.
    """
    cleaned = raw.strip().replace(",", ".")
    if not cleaned:
        raise InvalidInputError(
            "Пустой ввод. Введите число, например 36.6 или 36,6."
        )

    try:
        value = float(cleaned)
    except ValueError as exc:
        raise InvalidInputError(
            f"Некорректное число: {raw!r}. Пример: 36.6 или 36,6."
        ) from exc

    if math.isnan(value) or math.isinf(value):
        raise InvalidInputError(
            f"Значение {raw!r} не является конечным числом."
        )
    return value


def validate_above_absolute_zero(value: float, scale: TemperatureScale) -> None:
    """Проверить, что значение не ниже абсолютного нуля.
    Проверка делается в градусах Цельсия — так у нас один порог
    и одна точка сравнения для всех шкал. Порог для исходной шкалы
    вычисляется функцией absolute_zero_in только для текста сообщения.
    Args:
        value: значение в исходной шкале.
        scale: исходная шкала.
    Raises:
        BelowAbsoluteZeroError: если значение ниже абсолютного нуля
            (с учётом допуска на ошибки округления).
    """
    value_celsius = to_celsius(value, scale)
    if value_celsius < ABSOLUTE_ZERO_C - _ABSOLUTE_ZERO_EPSILON:
        raise BelowAbsoluteZeroError(
            value=value,
            scale_code=scale.short_name,
            min_allowed=absolute_zero_in(scale),
        )


def parse_menu_choice(raw: str, allowed: range) -> int:
    """Разобрать номер пункта нумерованного меню.
    Используется в CLI для меню вида "1. Цельсий 2. Фаренгейт 3. Кельвин".
    Защищает от неверного диапазона: если в меню 3 пункта, а пользователь
    ввёл 7, будет InvalidInputError с понятным текстом.
    Args:
        raw: строка, введённая пользователем.
        allowed: диапазон допустимых номеров, например range(1, 4) для 1..3.
    Returns:
        Целое число из allowed.
    Raises:
        InvalidInputError: если ввод не является целым числом или вне диапазона.
    """
    cleaned = raw.strip()
    bounds = f"от {allowed.start} до {allowed.stop - 1}"
    if not cleaned:
        raise InvalidInputError(f"Пустой ввод. Введите номер {bounds}.")

    try:
        choice = int(cleaned)
    except ValueError as exc:
        raise InvalidInputError(f"Нужно ввести целое число {bounds}.") from exc

    if choice not in allowed:
        raise InvalidInputError(
            f"Номер {choice} вне диапазона. Допустимо: {bounds}."
        )
    return choice