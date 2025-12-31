"""
FastAPI SQLAlchemy Query - Dynamic filters and ordering for FastAPI + SQLAlchemy.

This library provides a declarative way to add filtering and ordering
capabilities to your FastAPI endpoints with SQLAlchemy models.

Example:
    from fastapi import Depends, FastAPI
    from fastapi_sa_query import filter_, filter_by_fields, order_by_fields
    from fastapi_sa_query.func import eq, like, gte, lte

    app = FastAPI()

    @app.get("/users")
    def get_users(
        filter_by=Depends(filter_by_fields({
            "name": filter_(User.name, (eq, like)),
            "age": filter_(User.age, (gte, lte)),
        })),
        order_by=Depends(order_by_fields({
            "id": User.id,
            "name": User.name,
        })),
    ):
        return db.query(User).filter(*filter_by).order_by(*order_by).all()
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Union

from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from fastapi_sa_query.filter import (
    FilterError,
    InvalidFieldError,
    InvalidOperatorError,
    filter_by_fields,
)
from fastapi_sa_query.order import order_by_fields

__version__ = "0.1.0"

__all__ = [
    "FilterError",
    "FilterType",
    "InvalidFieldError",
    "InvalidOperatorError",
    "filter_",
    "filter_by_fields",
    "order_by_fields",
]

ColumnType = Union[ColumnElement[Any], InstrumentedAttribute[Any]]


@dataclass
class FilterType:
    """
    Configuration for a single filterable field.

    Attributes:
        field: SQLAlchemy column or instrumented attribute to filter on.
        operators: Dictionary mapping operator names to operator functions.
        cast_type: Optional callable to convert query parameter values.
        query_param_type: Optional type hint for the query parameter.
    """

    field: ColumnType
    operators: dict[str, Callable[..., Any]]
    cast_type: Callable[..., Any] | None = None
    query_param_type: type[Any] | None = None


def _noop(x: Any) -> Any:
    """Identity function for default cast_type."""
    return x


def filter_(
    field: ColumnType,
    operators: tuple[Callable[..., Any], ...],
    cast_type: Callable[..., Any] | None = None,
    query_param_type: type[Any] | None = None,
) -> FilterType:
    """
    Create a filter configuration for a field.

    Args:
        field: SQLAlchemy column to filter on.
        operators: Tuple of operator functions (eq, like, gte, etc.).
        cast_type: Optional callable to convert query parameter values.
        query_param_type: Optional type hint override for the query parameter.

    Returns:
        FilterType configuration object.

    Example:
        filter_(User.name, (eq, like, ilike))
        filter_(User.age, (gte, lte, in_))
        filter_(Order.user_id, (eq,), cast_type=UUID)
    """
    return FilterType(
        field=field,
        operators={func.__name__.strip("_"): func for func in operators},
        cast_type=cast_type or _noop,
        query_param_type=query_param_type,
    )
