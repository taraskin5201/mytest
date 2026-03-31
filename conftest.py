import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base
from deps import get_db, get_current_user
from main import app
import models
from auth import hash_password

# --- In-memory SQLite for tests ---
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Clean tables before each test."""
    yield
    db = TestingSessionLocal()
    db.query(models.Article).delete()
    db.query(models.User).delete()
    db.query(models.Role).delete()
    db.commit()
    db.close()


@pytest.fixture
def db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


def make_role(db, name="user"):
    role = models.Role(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def make_user(db, username="testuser", password="pass", role=None):
    if role is None:
        role = make_role(db, "user")
    user = models.User(
        username=username,
        hashed_password=hash_password(password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_article(db, owner, title="Test Article", content="Test content"):
    article = models.Article(title=title, content=content, owner_id=owner.id)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_client_for_user(user):
    """Return TestClient with get_current_user overridden to return given user."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
