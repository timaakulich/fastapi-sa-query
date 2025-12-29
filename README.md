# fastapi-sa-query

Dynamic query filters and ordering for FastAPI + SQLAlchemy.

## Installation

```bash
pip install fastapi sqlalchemy
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
    filters=Depends(filter_by_fields({
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
    query = db.query(User).filter(*filters).order_by(*order_by)
    return query.all()
```

## API Usage

### Filtering

Filters are passed as query parameters with the format `field__operator`:

```
GET /users?name__eq=Alice
GET /users?age__gte=25
GET /users?age__lte=30
GET /users?name__like=ali
GET /users?name__ilike=ALICE
GET /users?score__is_null=true
```

List operators use `[]` suffix:

```
GET /users?age__in[]=25&age__in[]=30
```

### Ordering

Use `order_by[]` parameter. Prefix with `-` for descending:

```
GET /users?order_by[]=name
GET /users?order_by[]=-age
GET /users?order_by[]=age&order_by[]=-name
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
| `contained_by` | Array contained by (PostgreSQL) | `?tags__contained_by[]=a&tags__contained_by[]=b` |

## Advanced Usage

### Custom Type Casting

```python
from uuid import UUID

filters = {
    "user_id": filter_(
        Order.user_id,
        (eq,),
        cast_type=UUID,  # Convert string to UUID
    ),
}
```

### Custom Query Parameter Type

```python
filters = {
    "status": filter_(
        Order.status,
        (eq, in_),
        query_param_type=str,  # Override detected type
    ),
}
```

### Combining Filters

Multiple filters are combined with AND:

```
GET /users?age__gte=25&age__lte=35&name__ilike=a
```

### Filtering and Ordering on Joined Tables

You can filter and order by columns from related tables. Just add the join in your query and reference the related model's columns:

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    views: Mapped[int] = mapped_column(Integer)

    author: Mapped["User"] = relationship("User")


@app.get("/posts")
def get_posts(
    db: Session = Depends(get_db),
    filters=Depends(filter_by_fields({
        # Post filters
        "title": filter_(Post.title, (eq, like, ilike)),
        "views": filter_(Post.views, (eq, gte, lte)),
        # Joined User filters
        "author_name": filter_(User.name, (eq, like, ilike)),
        "author_age": filter_(User.age, (eq, gte, lte)),
        "author_email": filter_(User.email, (like, ilike)),
    })),
    order_by=Depends(order_by_fields({
        "id": Post.id,
        "title": Post.title,
        "views": Post.views,
        # Joined User ordering
        "author_name": User.name,
        "author_age": User.age,
    })),
):
    # Add .join(User) for joined filters/ordering
    query = db.query(Post).join(User).filter(*filters).order_by(*order_by)
    return query.all()
```

API usage:

```
# Filter posts by author's name
GET /posts?author_name__eq=Alice

# Filter by author age range
GET /posts?author_age__gte=25&author_age__lte=35

# Combine post and author filters
GET /posts?views__gte=100&author_name__like=ali

# Order by author's name
GET /posts?order_by[]=author_name

# Order by author age descending
GET /posts?order_by[]=-author_age

# Filter and order together
GET /posts?author_age__gte=30&order_by[]=-views
```

## Complete Example

```python
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker

from fastapi_sa_query import filter_, filter_by_fields, order_by_fields
from fastapi_sa_query.func import eq, gte, lte, gt, lt, like, ilike, in_, is_null


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    age: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)


engine = create_engine("sqlite:///./app.db")
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


@app.get("/users")
def get_users(
    db: Session = Depends(get_db),
    filters=Depends(filter_by_fields({
        "name": filter_(User.name, (eq, like, ilike)),
        "email": filter_(User.email, (eq, like, ilike)),
        "age": filter_(User.age, (eq, gte, lte, gt, lt, in_)),
        "created_at": filter_(User.created_at, (eq, gte, lte)),
        "score": filter_(User.score, (eq, gte, lte, is_null)),
    })),
    order_by=Depends(order_by_fields({
        "id": User.id,
        "name": User.name,
        "age": User.age,
        "created_at": User.created_at,
    }, default=User.id)),
) -> List[dict]:
    query = db.query(User).filter(*filters).order_by(*order_by)
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "age": u.age,
            "created_at": u.created_at.isoformat(),
            "score": u.score,
        }
        for u in query.all()
    ]
```

## Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```

## License

MIT

