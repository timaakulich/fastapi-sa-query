

from typing import Any, List

from sqlalchemy import func
from sqlalchemy.sql.elements import ColumnElement


def _strtobool(val: str) -> bool:
    val = val.lower()
    if val in {"true", "1", "yes", "on"}:
        return True
    elif val in {"false", "0", "no", "off"}:
        return False
    else:
        raise ValueError(f"Invalid boolean string: {val!r}")


def gte(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    return x >= y


def lte(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    return x <= y


def gt(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    return x > y


def lt(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    return x < y


def eq(x: ColumnElement[Any], y: Any) -> ColumnElement[bool]:
    return x == y


def like(x: ColumnElement[str], y: str) -> ColumnElement[bool]:
    return x.like("%{}%".format(y))


def ilike(x: ColumnElement[str], y: str) -> ColumnElement[bool]:
    return x.ilike("%{}%".format(y))


def in_(x: ColumnElement[Any], y: List[Any]) -> ColumnElement[bool]:
    return x.in_(y)


def contained_by(x: ColumnElement[Any], y: List[Any]) -> ColumnElement[bool]:
    return x.contained_by(y)


def contains(x: ColumnElement[Any], y: List[Any]) -> ColumnElement[bool]:
    return x.contains(list(y))


def contains_like(x: ColumnElement[Any], y: str) -> ColumnElement[bool]:
    return func.array_to_string(x, ",").like("%{}%".format(y))


def empty_list(x: ColumnElement[Any], y: str) -> ColumnElement[bool]:
    return x == [] if _strtobool(y) else x != []


def is_null(x: ColumnElement[Any], y: bool) -> ColumnElement[bool]:
    return x.is_(None) if y else x.isnot(None)


FILTERS_LIST = (
    gte, lte, gt, lt, eq, like, ilike, in_,
    contained_by, contains, contains_like, empty_list, is_null
)

LIST_OPERATORS = {in_, contained_by, contains}

OPERATORS_TYPES = {
    is_null: bool
}
