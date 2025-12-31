"""
Example FastAPI application demonstrating fastapi-sa-query usage.

Run with:
    uvicorn example_app:app --reload

API docs available at:
    http://127.0.0.1:8000/docs
"""

from collections.abc import Generator
from datetime import datetime
from decimal import Decimal

import fastapi
from fastapi import Depends, FastAPI
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from fastapi_sa_query import filter_, filter_by_fields, order_by_fields
from fastapi_sa_query.func import eq, gt, gte, ilike, in_, is_null, like, lt, lte

# --- Models ---


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

    posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(String(1000))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    views: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime)

    author: Mapped["User"] = relationship("User", back_populates="posts")


# --- Database ---


engine = create_engine(
    "sqlite:///./example.db",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(engine)


def seed_db() -> None:
    db = SessionLocal()

    if db.query(User).count() > 0:
        db.close()
        return

    users = [
        User(
            id=1,
            name="Alice Johnson",
            email="alice@example.com",
            age=28,
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            score=95,
        ),
        User(
            id=2,
            name="Bob Smith",
            email="bob@example.com",
            age=35,
            created_at=datetime(2024, 2, 20, 12, 0, 0),
            score=82,
        ),
        User(
            id=3,
            name="Charlie Brown",
            email="charlie@test.org",
            age=42,
            created_at=datetime(2024, 3, 10, 8, 0, 0),
            score=None,
        ),
        User(
            id=4,
            name="Diana Prince",
            email="diana@example.com",
            age=31,
            created_at=datetime(2024, 4, 5, 14, 0, 0),
            score=91,
        ),
        User(
            id=5,
            name="Eve Wilson",
            email="eve@example.com",
            age=25,
            created_at=datetime(2024, 5, 1, 9, 0, 0),
            score=None,
        ),
    ]
    db.add_all(users)
    db.commit()

    posts = [
        Post(
            id=1,
            title="Getting Started with Python",
            content="Python is a versatile programming language...",
            author_id=1,
            views=1500,
            rating=Decimal("4.8"),
            published_at=datetime(2024, 1, 20, 10, 0, 0),
        ),
        Post(
            id=2,
            title="FastAPI Best Practices",
            content="Learn how to build production-ready APIs...",
            author_id=1,
            views=2300,
            rating=Decimal("4.9"),
            published_at=datetime(2024, 2, 15, 12, 0, 0),
        ),
        Post(
            id=3,
            title="SQLAlchemy ORM Guide",
            content="Understanding object-relational mapping...",
            author_id=2,
            views=1800,
            rating=Decimal("4.5"),
            published_at=datetime(2024, 3, 1, 9, 0, 0),
        ),
        Post(
            id=4,
            title="Advanced Python Patterns",
            content="Metaclasses, decorators, and more...",
            author_id=3,
            views=950,
            rating=None,
            published_at=datetime(2024, 3, 20, 14, 0, 0),
        ),
        Post(
            id=5,
            title="Testing with Pytest",
            content="Write better tests for your applications...",
            author_id=2,
            views=1200,
            rating=Decimal("4.3"),
            published_at=datetime(2024, 4, 10, 11, 0, 0),
        ),
        Post(
            id=6,
            title="Docker for Developers",
            content="Containerize your applications...",
            author_id=4,
            views=2100,
            rating=Decimal("4.7"),
            published_at=datetime(2024, 5, 5, 8, 0, 0),
        ),
        Post(
            id=7,
            title="Async Python Deep Dive",
            content="Master asyncio and concurrent programming...",
            author_id=5,
            views=1650,
            rating=Decimal("4.6"),
            published_at=datetime(2024, 6, 1, 15, 0, 0),
        ),
    ]
    db.add_all(posts)
    db.commit()
    db.close()


# --- FastAPI App ---


async def lifespan(app: fastapi.FastAPI) -> None:
    init_db()
    seed_db()
    yield


app = FastAPI(
    title="FastAPI SA Query Example",
    description="Demo application for fastapi-sa-query library",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/users", tags=["Users"])
def get_users(
    db: Session = Depends(get_db),
    filter_by=Depends(filter_by_fields({
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
        "score": User.score,
    }, default=User.id)),
) -> list[dict]:
    """
    Get users with filters and ordering.

    **Filter examples:**
    - `?name__eq=Alice` - exact match
    - `?name__like=ali` - contains (case-sensitive)
    - `?name__ilike=ALI` - contains (case-insensitive)
    - `?age__gte=25&age__lte=35` - age range
    - `?age__in[]=25&age__in[]=30` - age in list
    - `?score__is_null=true` - null check

    **Order examples:**
    - `?order_by[]=name` - ascending
    - `?order_by[]=-age` - descending
    """
    query = db.query(User).filter(*filter_by).order_by(*order_by)
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


@app.get("/posts", tags=["Posts"])
def get_posts(
    db: Session = Depends(get_db),
    filter_by=Depends(filter_by_fields({
        "title": filter_(Post.title, (eq, like, ilike)),
        "views": filter_(Post.views, (eq, gte, lte, gt, lt)),
        "rating": filter_(Post.rating, (eq, gte, lte, is_null), query_param_type=float),
        "published_at": filter_(Post.published_at, (eq, gte, lte)),
        # Joined User filters
        "author_name": filter_(User.name, (eq, like, ilike)),
        "author_age": filter_(User.age, (eq, gte, lte)),
        "author_email": filter_(User.email, (like, ilike)),
    })),
    order_by=Depends(order_by_fields({
        "id": Post.id,
        "title": Post.title,
        "views": Post.views,
        "rating": Post.rating,
        "published_at": Post.published_at,
        # Joined User ordering
        "author_name": User.name,
        "author_age": User.age,
    }, default=Post.id)),
) -> list[dict]:
    """
    Get posts with filters and ordering (including joined author data).

    **Post filter examples:**
    - `?title__ilike=python` - title contains
    - `?views__gte=1000` - views >= 1000
    - `?rating__is_null=false` - has rating

    **Joined author filter examples:**
    - `?author_name__eq=Alice Johnson` - by author name
    - `?author_age__gte=30` - by author age
    - `?author_email__like=example.com` - by author email

    **Order examples:**
    - `?order_by[]=-views` - by views descending
    - `?order_by[]=author_name` - by author name
    """
    query = db.query(Post).join(User).filter(*filter_by).order_by(*order_by)
    return [
        {
            "id": p.id,
            "title": p.title,
            "content": p.content,
            "author": {
                "id": p.author.id,
                "name": p.author.name,
                "age": p.author.age,
            },
            "views": p.views,
            "rating": float(p.rating) if p.rating else None,
            "published_at": p.published_at.isoformat(),
        }
        for p in query.all()
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

