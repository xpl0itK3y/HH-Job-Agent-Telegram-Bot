from collections.abc import Callable
from enum import Enum as PyEnum

from sqlalchemy import Enum


def values_enum(enum_cls: type[PyEnum], *, name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        values_callable=lambda enum_values: [item.value for item in enum_values],
        validate_strings=True,
    )
