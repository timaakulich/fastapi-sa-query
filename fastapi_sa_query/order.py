
from typing import Callable, Dict, Optional, Tuple, Union, Any

from fastapi import Query
from sqlalchemy import asc, desc
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

__all__ = ("order_by_fields",)

ColumnType = Union[ColumnElement[Any], InstrumentedAttribute[Any]]


def order_by_fields(
    available_fields: Dict[str, ColumnType],
    default: Optional[Union[ColumnType, Tuple[ColumnType, ...]]] = None
) -> Callable:
    _fields = list(available_fields.keys())
    _fields.extend([f"-{_field}" for _field in _fields])

    def order_dependence(
        order_by_params: list = Query(
            [],
            alias="order_by[]",
            description=f"Available fields: {', '.join(_fields)}"
        )
    ) -> Tuple[ColumnElement[Any], ...]:
        result_fields = []
        for field in order_by_params:
            direction = desc if field.startswith("-") else asc
            field = field.lstrip("-")
            if field in available_fields:
                result_fields.append(direction(available_fields[field]))

        _order_by = tuple(result_fields)
        if not _order_by and default is not None:
            _order_by = (default,) if not isinstance(default, tuple) else default
        return _order_by

    return order_dependence
