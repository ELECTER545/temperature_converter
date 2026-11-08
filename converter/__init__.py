"""Пакет конвертера температур.
Публичный API пакета — то, что можно импортировать как `from converter import X`.
Внутренние модули (например, `converter._helpers`) не считаются частью API
и могут меняться без предупреждения.
"""

from __future__ import annotations

from converter.conversion import (
    ABSOLUTE_ZERO_C,
    absolute_zero_in,
    convert,
    from_celsius,
    to_celsius,
)
from converter.exceptions import (
    BelowAbsoluteZeroError,
    ConverterError,
    HistoryError,
    InvalidInputError,
)
from converter.history import (
    VALUE_DECIMALS,
    HistoryRecord,
    HistoryStorage,
)
from converter.scales import TemperatureScale

# __all__ фиксирует, что считается публичным при `from converter import *`
# и служит документацией API. Внутренние помощники сюда не попадают.
__all__ = [
    "ABSOLUTE_ZERO_C",
    "BelowAbsoluteZeroError",
    "ConverterError",
    "HistoryError",
    "HistoryRecord",
    "HistoryStorage",
    "InvalidInputError",
    "TemperatureScale",
    "VALUE_DECIMALS",
    "absolute_zero_in",
    "convert",
    "from_celsius",
    "to_celsius",
]
