"""
Filter dependency generator for FastAPI endpoints.

This module provides the filter_by_fields function that creates
a FastAPI dependency for handling query parameter filters.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import make_dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Union

from fastapi import Query
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from fastapi_sa_query.func import LIST_OPERATORS, OPERATORS_TYPES

if TYPE_CHECKING:
    from fastapi_sa_query import FilterType

ColumnType = Union[ColumnElement[Any], InstrumentedAttribute[Any]]


class FilterError(Exception):
    """Base exception for filter-related errors."""

    pass


class InvalidFieldError(FilterError):
    """Raised when an invalid field name is used."""

    pass


class InvalidOperatorError(FilterError):
    """Raised when an invalid operator is used for a field."""

    pass


def filter_by_fields(available_fields: dict[str, FilterType]) -> type[Any]:
    """
    Create a FastAPI dependency class for filtering.

    This function generates a dataclass with query parameters for each
    field/operator combination defined in available_fields.

    Args:
        available_fields: Dictionary mapping field names to FilterType configs.

    Returns:
        A dataclass type that can be used as a FastAPI dependency.

    Example:
        @app.get("/users")
        def get_users(
            filter_by=Depends(filter_by_fields({
                "name": filter_(User.name, (eq, like)),
                "age": filter_(User.age, (gte, lte)),
            }))
        ):
            return db.query(User).filter(*filter_by).all()
    """
    field_definitions: list[tuple[str, type, Any]] = []

    for field_name, field_filter in available_fields.items():
        for operator_name, operator_func in field_filter.operators.items():
            is_list = operator_func in LIST_OPERATORS
            field_type = (
                OPERATORS_TYPES.get(operator_func)
                or field_filter.query_param_type
                or field_filter.field.type.python_type
            )
            name = f"{field_name}__{operator_name}"
            field_definitions.append(
                (
                    name,
                    list[field_type] if is_list else field_type,  # type: ignore[valid-type]
                    Query(None, alias=f"{name}{'[]' if is_list else ''}"),
                )
            )

    def __iter__(self: Any) -> Iterator[ColumnElement[Any]]:
        _filter_query: list[ColumnElement[Any]] = []
        for _field in self.__dataclass_fields__:
            if (value := getattr(self, _field, None)) is None:
                continue
            if isinstance(value, datetime):
                value = value.replace(tzinfo=None)

            _field_name, operator = _field.rsplit("__", 1)

            if _field_name not in available_fields:
                raise InvalidFieldError(
                    f"Unknown filter field: {_field_name!r}. "
                    f"Available fields: {list(available_fields.keys())}"
                )

            field_config = available_fields[_field_name]

            if operator not in field_config.operators:
                raise InvalidOperatorError(
                    f"Invalid operator {operator!r} for field {_field_name!r}. "
                    f"Available operators: {list(field_config.operators.keys())}"
                )

            cast_type = field_config.cast_type
            _filter_query.append(
                field_config.operators[operator](
                    field_config.field, cast_type(value)  # type: ignore[misc]
                )
            )
        return iter(_filter_query)

    result = make_dataclass(
        "FilterQueryParams",
        field_definitions,
        namespace={"__iter__": __iter__},
    )

    return result
