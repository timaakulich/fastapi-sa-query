"""
Ordering dependency generator for FastAPI endpoints.

This module provides the order_by_fields function that creates
a FastAPI dependency for handling query parameter ordering.
"""

from collections.abc import Callable
from typing import Any, Union

from fastapi import Query
from sqlalchemy import asc, desc
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

__all__ = ("order_by_fields",)

ColumnType = Union[ColumnElement[Any], InstrumentedAttribute[Any]]


def order_by_fields(
    available_fields: dict[str, ColumnType],
    default: ColumnType | tuple[ColumnType, ...] | None = None,
) -> Callable[..., tuple[ColumnElement[Any], ...]]:
    """
    Create a FastAPI dependency for ordering query results.

    Args:
        available_fields: Dictionary mapping field names to SQLAlchemy columns.
        default: Optional default ordering if none specified.

    Returns:
        A dependency function that returns a tuple of order_by clauses.

    Example:
        @app.get("/users")
        def get_users(
            order_by=Depends(order_by_fields({
                "id": User.id,
                "name": User.name,
                "age": User.age,
            }, default=User.id))
        ):
            return db.query(User).order_by(*order_by).all()

    Usage:
        GET /users?order_by[]=name      # ascending by name
        GET /users?order_by[]=-age      # descending by age
        GET /users?order_by[]=age&order_by[]=-name  # multiple
    """
    _fields = list(available_fields.keys())
    _fields.extend([f"-{_field}" for _field in _fields])

    def order_dependence(
        order_by_params: list[str] = Query(
            [], alias="order_by[]", description=f"Available fields: {', '.join(_fields)}"
        ),
    ) -> tuple[ColumnElement[Any], ...]:
        result_fields: list[ColumnElement[Any]] = []
        for field in order_by_params:
            direction = desc if field.startswith("-") else asc
            field = field.lstrip("-")
            if field in available_fields:
                result_fields.append(direction(available_fields[field]))

        _order_by = tuple(result_fields)
        if not _order_by and default is not None:
            _order_by = (default,) if not isinstance(default, tuple) else default  # type: ignore[assignment]
        return _order_by

    return order_dependence
