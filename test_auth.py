import pytest
from fastapi.testclient import TestClient
from deps import get_db
from main import app
from conftest import (
    override_get_db, TestingSessionLocal,
    make_role, make_user
)

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ===================== AUTH TESTS =====================

class TestLogin:
    def test_login_success(self, client, db):
        role = make_role(db, "user")
        make_user(db, "loginuser", "mypassword", role)

        resp = client.post("/auth/login", data={
            "username": "loginuser",
            "password": "mypassword"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client, db):
        role = make_role(db, "user")
        make_user(db, "loginuser2", "correctpass", role)

        resp = client.post("/auth/login", data={
            "username": "loginuser2",
            "password": "wrongpass"
        })
        assert resp.status_code == 400

    def test_login_nonexistent_user(self, client):
        resp = client.post("/auth/login", data={
            "username": "nobody",
            "password": "pass"
        })
        assert resp.status_code == 400

    def test_login_returns_bearer_token(self, client, db):
        role = make_role(db, "user")
        make_user(db, "tokenuser", "tokenpass", role)

        resp = client.post("/auth/login", data={
            "username": "tokenuser",
            "password": "tokenpass"
        })
        assert resp.status_code == 200
        assert resp.json()["access_token"] is not None
