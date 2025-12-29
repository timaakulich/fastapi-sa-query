
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple, Type, Any, Union

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from fastapi_sa_query.func import FILTERS_LIST


from fastapi_sa_query.filter import (
    filter_by_fields,
    FilterError,
    InvalidFieldError,
    InvalidOperatorError,
)
from fastapi_sa_query.order import order_by_fields


__all__ = [
    "filter_",
    "filter_by_fields",
    "order_by_fields",
    "FilterError",
    "InvalidFieldError",
    "InvalidOperatorError",
    "FilterType",
]

ColumnType = Union[ColumnElement[Any], InstrumentedAttribute[Any]]


@dataclass
class FilterType:
    field: ColumnType
    operators: Dict[str, Callable]
    cast_type: Optional[Callable] = None
    query_param_type: Optional[Type] = None


def __noop(x):
    return x


def filter_(
    field,
    operators: Tuple[Callable, ...],
    cast_type: Optional[Callable] = None,
    query_param_type: Optional[Type] = None,
) -> FilterType:
    return FilterType(
        field=field,
        operators={func.__name__.strip("_"): func for func in operators},
        cast_type=cast_type or __noop,
        query_param_type=query_param_type,
    )
