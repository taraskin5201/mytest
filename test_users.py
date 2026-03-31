import pytest
from conftest import (
    make_role, make_user, get_client_for_user,
    TestingSessionLocal
)


@pytest.fixture
def db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


# ===================== USERS TESTS =====================

class TestGetUsers:
    def test_admin_can_get_users(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admin1", "pass", admin_role)
        make_user(db, "user1", "pass", make_role(db, "user"))

        client = get_client_for_user(admin)
        resp = client.get("/users")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_non_admin_cannot_get_users(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "plainuser", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.get("/users")
        assert resp.status_code == 403

    def test_get_users_with_search(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admin2", "pass", admin_role)
        make_user(db, "alice", "pass", make_role(db, "user"))
        make_user(db, "bob", "pass", make_role(db, "user"))

        client = get_client_for_user(admin)
        resp = client.get("/users?q=alice")
        assert resp.status_code == 200
        data = resp.json()
        assert all("alice" in u["username"].lower() for u in data)

    def test_get_users_pagination(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "adminpag", "pass", admin_role)
        user_role = make_role(db, "user")
        for i in range(5):
            make_user(db, f"puser{i}", "pass", user_role)

        client = get_client_for_user(admin)
        resp = client.get("/users?limit=2&offset=0")
        assert resp.status_code == 200
        assert len(resp.json()) <= 2


class TestCreateUser:
    def test_admin_can_create_user(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admincreate", "pass", admin_role)
        user_role = make_role(db, "user")

        client = get_client_for_user(admin)
        resp = client.post("/users", json={
            "username": "newuser",
            "password": "newpass",
            "role_id": user_role.id
        })
        assert resp.status_code == 200

    def test_non_admin_cannot_create_user(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "notadmin", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.post("/users", json={
            "username": "anotheruser",
            "password": "pass",
            "role_id": user_role.id
        })
        assert resp.status_code == 403


class TestUpdateUser:
    def test_admin_can_update_user(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "adminupd", "pass", admin_role)
        user_role = make_role(db, "user")
        target = make_user(db, "targetuser", "pass", user_role)

        client = get_client_for_user(admin)
        resp = client.put(f"/users/{target.id}", json={"username": "updatedname"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "updatedname"

    def test_update_nonexistent_user(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admindelete", "pass", admin_role)

        client = get_client_for_user(admin)
        resp = client.put("/users/99999", json={"username": "x"})
        assert resp.status_code == 404

    def test_non_admin_cannot_update_user(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "userupd", "pass", user_role)
        target = make_user(db, "target2", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.put(f"/users/{target.id}", json={"username": "hacked"})
        assert resp.status_code == 403


class TestDeleteUser:
    def test_admin_can_delete_user(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admindel", "pass", admin_role)
        user_role = make_role(db, "user")
        target = make_user(db, "todelete", "pass", user_role)

        client = get_client_for_user(admin)
        resp = client.delete(f"/users/{target.id}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_delete_nonexistent_user(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admindel2", "pass", admin_role)

        client = get_client_for_user(admin)
        resp = client.delete("/users/99999")
        assert resp.status_code == 404

    def test_non_admin_cannot_delete_user(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "userdel", "pass", user_role)
        target = make_user(db, "target3", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.delete(f"/users/{target.id}")
        assert resp.status_code == 403
