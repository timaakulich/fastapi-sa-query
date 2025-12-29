from datetime import datetime
from typing import Generator, List

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, Integer, DateTime, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi_sa_query import filter_, filter_by_fields, order_by_fields
from fastapi_sa_query.func import gte, lte, eq, like, ilike, in_, gt, lt, is_null


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


USER_FILTERS = {
    "name": filter_(User.name, (eq, like, ilike)),
    "email": filter_(User.email, (eq, like, ilike)),
    "age": filter_(User.age, (eq, gte, lte, gt, lt, in_)),
    "created_at": filter_(User.created_at, (eq, gte, lte)),
    "score": filter_(User.score, (eq, gte, lte, is_null)),
}

USER_ORDER_FIELDS = {
    "id": User.id,
    "name": User.name,
    "age": User.age,
    "created_at": User.created_at,
}


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/users")
    def get_users(
        db: Session = Depends(get_db),
        filters: filter_by_fields(USER_FILTERS) = Depends(),
        order_by: tuple = Depends(order_by_fields(USER_ORDER_FIELDS, default=User.id)),
    ) -> List[dict]:
        query = db.query(User).filter(*filters).order_by(*order_by)

        users = query.all()
        return [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "age": u.age,
                "created_at": u.created_at.isoformat(),
                "score": u.score,
            }
            for u in users
        ]

    return app


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def seed_users(setup_db) -> Generator[List[User], None, None]:
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

    yield users

    db.query(User).delete()
    db.commit()
    db.close()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
