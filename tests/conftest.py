from collections.abc import Generator
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from fastapi_sa_query import filter_, filter_by_fields, order_by_fields
from fastapi_sa_query.func import eq, gt, gte, ilike, in_, is_null, like, lt, lte


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


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/users")
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
        }, default=User.id)),
    ) -> list[dict]:
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

    @app.get("/posts")
    def get_posts(
        db: Session = Depends(get_db),
        filter_by=Depends(filter_by_fields({
            "title": filter_(Post.title, (eq, like, ilike)),
            "views": filter_(Post.views, (eq, gte, lte, gt, lt)),
            "rating": filter_(Post.rating, (eq, gte, lte, is_null), query_param_type=float),
            "published_at": filter_(Post.published_at, (eq, gte, lte)),
            # Filters on joined User table
            "author_name": filter_(User.name, (eq, like, ilike)),
            "author_age": filter_(User.age, (eq, gte, lte)),
            "author_email": filter_(User.email, (like, ilike)),
        })),
        order_by=Depends(order_by_fields({
            "id": Post.id,
            "title": Post.title,
            "views": Post.views,
            "published_at": Post.published_at,
            "author_name": User.name,
            "author_age": User.age,
        }, default=Post.id)),
    ) -> list[dict]:
        query = db.query(Post).join(User).filter(*filter_by).order_by(*order_by)
        return [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content,
                "author_id": p.author_id,
                "author_name": p.author.name,
                "author_age": p.author.age,
                "views": p.views,
                "rating": float(p.rating) if p.rating else None,
                "published_at": p.published_at.isoformat(),
            }
            for p in query.all()
        ]

    return app


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def seed_data(setup_db) -> Generator[dict, None, None]:
    db = SessionLocal()

    users = [
        User(
            id=1,
            name="Alice",
            email="alice@example.com",
            age=25,
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            score=100,
        ),
        User(
            id=2,
            name="Bob",
            email="bob@example.com",
            age=30,
            created_at=datetime(2024, 2, 20, 12, 0, 0),
            score=85,
        ),
        User(
            id=3,
            name="Charlie",
            email="charlie@test.org",
            age=35,
            created_at=datetime(2024, 3, 10, 8, 0, 0),
            score=None,
        ),
        User(
            id=4,
            name="Diana",
            email="diana@example.com",
            age=28,
            created_at=datetime(2024, 4, 5, 14, 0, 0),
            score=92,
        ),
        User(
            id=5,
            name="alice_smith",
            email="asmith@example.com",
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
            title="Python Tips",
            content="Learn Python basics",
            author_id=1,
            views=150,
            rating=Decimal("4.5"),
            published_at=datetime(2024, 1, 20, 10, 0, 0),
        ),
        Post(
            id=2,
            title="FastAPI Guide",
            content="Building APIs with FastAPI",
            author_id=1,
            views=300,
            rating=Decimal("4.8"),
            published_at=datetime(2024, 2, 15, 12, 0, 0),
        ),
        Post(
            id=3,
            title="SQLAlchemy Basics",
            content="ORM fundamentals",
            author_id=2,
            views=200,
            rating=Decimal("4.2"),
            published_at=datetime(2024, 3, 1, 9, 0, 0),
        ),
        Post(
            id=4,
            title="Advanced Python",
            content="Metaclasses and decorators",
            author_id=3,
            views=100,
            rating=None,
            published_at=datetime(2024, 3, 20, 14, 0, 0),
        ),
        Post(
            id=5,
            title="Testing Guide",
            content="Unit and integration testing",
            author_id=2,
            views=180,
            rating=Decimal("4.0"),
            published_at=datetime(2024, 4, 10, 11, 0, 0),
        ),
        Post(
            id=6,
            title="Docker Basics",
            content="Containerization intro",
            author_id=4,
            views=250,
            rating=Decimal("4.6"),
            published_at=datetime(2024, 5, 5, 8, 0, 0),
        ),
    ]
    db.add_all(posts)
    db.commit()

    yield {"users": users, "posts": posts}

    db.query(Post).delete()
    db.query(User).delete()
    db.commit()
    db.close()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
