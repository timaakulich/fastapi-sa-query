"""
Filter operator functions for SQLAlchemy queries.

This module provides comparison and filtering functions that generate
SQLAlchemy WHERE clause expressions.

Available operators:
    - eq: Equality (==)
    - gt, gte: Greater than (>), greater than or equal (>=)
    - lt, lte: Less than (<), less than or equal (<=)
    - like, ilike: Pattern matching (case-sensitive/insensitive)
    - in_: Value in list
    - is_null: NULL check
    - contains, contained_by: PostgreSQL array operators
    - contains_like, empty_list: PostgreSQL array helpers
"""

from typing import Any

from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement


def _strtobool(val: str) -> bool:
    """Convert string to boolean."""
    val = val.lower()
    if val in {"true", "1", "yes", "on"}:
        return True
    elif val in {"false", "0", "no", "off"}:
        return False
    else:
        raise ValueError(f"Invalid boolean string: {val!r}")


def gte(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    """Greater than or equal comparison (>=)."""
    return x >= y  # type: ignore[no-any-return]


def lte(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    """Less than or equal comparison (<=)."""
    return x <= y  # type: ignore[no-any-return]


def gt(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    """Greater than comparison (>)."""
    return x > y  # type: ignore[no-any-return]


def lt(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    """Less than comparison (<)."""
    return x < y  # type: ignore[no-any-return]


def eq(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    """Equality comparison (==)."""
    return x == y  # type: ignore[no-any-return]


def like(x: ColumnElement[str], y: str) -> ColumnElement[bool]:
    """Case-sensitive LIKE pattern matching with wildcards."""
    return x.like(f"%{y}%")


def ilike(x: ColumnElement[str], y: str) -> ColumnElement[bool]:
    """Case-insensitive LIKE pattern matching with wildcards."""
    return x.ilike(f"%{y}%")


def in_(x: ColumnElement[Any], y: list[Any]) -> ColumnElement[bool]:
    """Check if value is in a list (SQL IN clause)."""
    return x.in_(y)


def contained_by(x: ColumnElement[Any], y: list[Any]) -> ColumnElement[bool]:
    """Check if array column is contained by the given list (PostgreSQL)."""
    return x.contained_by(y)  # type: ignore[no-any-return]


def contains(x: ColumnElement[Any], y: list[Any]) -> ColumnElement[bool]:
    """Check if array column contains all given values (PostgreSQL)."""
    return x.contains(list(y))


def contains_like(x: ColumnElement[Any], y: str) -> ColumnElement[bool]:
    """Search within array elements using LIKE pattern (PostgreSQL)."""
    return func.array_to_string(x, ",").like(f"%{y}%")


def empty_list(x: ColumnElement[Any], y: str) -> ColumnElement[bool]:
    """Check if array column is empty or not empty."""
    return x == [] if _strtobool(y) else x != []


def is_null(x: ColumnElement[Any], y: bool) -> ColumnElement[bool]:
    """Check if value is NULL or NOT NULL."""
    return x.is_(None) if y else x.isnot(None)


# All available filter operators
FILTERS_LIST = (
    gte,
    lte,
    gt,
    lt,
    eq,
    like,
    ilike,
    in_,
    contained_by,
    contains,
    contains_like,
    empty_list,
    is_null,
)

# Operators that accept list values
LIST_OPERATORS = {in_, contained_by, contains}

# Operators with specific parameter types
OPERATORS_TYPES: dict[Any, type] = {is_null: bool}
