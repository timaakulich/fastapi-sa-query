# fastapi-sa-query

[![PyPI version](https://badge.fury.io/py/fastapi-sa-query.svg)](https://badge.fury.io/py/fastapi-sa-query)
[![Python](https://img.shields.io/pypi/pyversions/fastapi-sa-query.svg)](https://pypi.org/project/fastapi-sa-query/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/fastapi-sa-query/workflows/Tests/badge.svg)](https://github.com/yourusername/fastapi-sa-query/actions)

Dynamic query filters and ordering for **FastAPI** + **SQLAlchemy 2.0**.

Build powerful, type-safe REST APIs with declarative filtering and sorting — no boilerplate required.

## Features

- 🎯 **Declarative filters** — define once, use everywhere
- 🔗 **Join support** — filter and sort by related table columns
- 📝 **Type-safe** — full type hints with `py.typed` marker
- 🚀 **Zero boilerplate** — works seamlessly with FastAPI's dependency injection
- 📖 **Auto-documented** — filters appear in OpenAPI/Swagger UI

## Installation

```bash
pip install fastapi-sa-query
```

## Quick Start

```python
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from fastapi_sa_query import filter_, filter_by_fields, order_by_fields
from fastapi_sa_query.func import eq, gte, lte, like, ilike, in_, is_null

app = FastAPI()


@app.get("/users")
def get_users(
    db: Session = Depends(get_db),
    filter_by=Depends(filter_by_fields({
        "name": filter_(User.name, (eq, like, ilike)),
        "age": filter_(User.age, (eq, gte, lte, in_)),
        "score": filter_(User.score, (eq, gte, lte, is_null)),
    })),
    order_by=Depends(order_by_fields({
        "id": User.id,
        "name": User.name,
        "age": User.age,
    }, default=User.id)),
):
    query = db.query(User).filter(*filter_by).order_by(*order_by)
    return query.all()
```

That's it! Your API now supports:

```
GET /users?name__like=john&age__gte=25&order_by[]=-age
```

## Usage

### Filtering

Filters use the format `field__operator`:

| Request | Description |
|---------|-------------|
| `?name__eq=Alice` | Exact match |
| `?age__gte=25` | Greater than or equal |
| `?age__lte=30` | Less than or equal |
| `?name__like=ali` | Contains (case-sensitive) |
| `?name__ilike=ALI` | Contains (case-insensitive) |
| `?score__is_null=true` | NULL check |
| `?age__in[]=25&age__in[]=30` | Value in list |

### Ordering

Use `order_by[]` parameter. Prefix with `-` for descending:

```
GET /users?order_by[]=name          # ascending
GET /users?order_by[]=-age          # descending
GET /users?order_by[]=age&order_by[]=-name  # multiple
```

### Combining Filters

Multiple filters are combined with AND:

```
GET /users?age__gte=25&age__lte=35&name__ilike=a
```

## Available Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `?name__eq=Alice` |
| `gt` | Greater than | `?age__gt=25` |
| `gte` | Greater than or equal | `?age__gte=25` |
| `lt` | Less than | `?age__lt=30` |
| `lte` | Less than or equal | `?age__lte=30` |
| `like` | Case-sensitive contains | `?name__like=ali` |
| `ilike` | Case-insensitive contains | `?name__ilike=ALI` |
| `in_` | Value in list | `?age__in[]=25&age__in[]=30` |
| `is_null` | Is NULL check | `?score__is_null=true` |
| `contains` | Array contains (PostgreSQL) | `?tags__contains[]=python` |
| `contained_by` | Array contained by (PostgreSQL) | `?tags__contained_by[]=a` |

## Advanced Usage

### Filtering on Joined Tables

Filter and order by columns from related tables:

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship("User")


@app.get("/posts")
def get_posts(
    db: Session = Depends(get_db),
    filter_by=Depends(filter_by_fields({
        # Post filters
        "title": filter_(Post.title, (eq, like, ilike)),
        "views": filter_(Post.views, (eq, gte, lte)),
        # Joined User filters
        "author_name": filter_(User.name, (eq, like, ilike)),
        "author_age": filter_(User.age, (eq, gte, lte)),
    })),
    order_by=Depends(order_by_fields({
        "id": Post.id,
        "title": Post.title,
        # Joined User ordering
        "author_name": User.name,
    })),
):
    query = db.query(Post).join(User).filter(*filter_by).order_by(*order_by)
    return query.all()
```

Usage:

```
GET /posts?author_name__eq=Alice
GET /posts?author_age__gte=30&order_by[]=-author_name
GET /posts?views__gte=100&author_name__like=ali
```

### Custom Type Casting

```python
from uuid import UUID

filter_by=Depends(filter_by_fields({
    "user_id": filter_(
        Order.user_id,
        (eq,),
        cast_type=UUID,  # Convert string to UUID
    ),
}))
```

### Custom Query Parameter Type

```python
filter_by=Depends(filter_by_fields({
    "rating": filter_(
        Post.rating,
        (eq, gte, lte),
        query_param_type=float,  # Override detected type
    ),
}))
```

## Example Application

Run the included example:

```bash
# Install dependencies
pip install fastapi-sa-query[dev]

# Run the example app
uvicorn example_app:app --reload
```

Open http://127.0.0.1:8000/docs to explore the API.

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/fastapi-sa-query.git
cd fastapi-sa-query

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy fastapi_sa_query
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
