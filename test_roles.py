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


# ===================== ROLES TESTS =====================

class TestCreateRole:
    def test_admin_can_create_role(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "adminrole", "pass", admin_role)

        client = get_client_for_user(admin)
        resp = client.post("/roles", json={"name": "moderator"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "moderator"

    def test_non_admin_cannot_create_role(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "userrole", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.post("/roles", json={"name": "superuser"})
        assert resp.status_code == 403


class TestGetRoles:
    def test_admin_can_get_roles(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admingetr", "pass", admin_role)

        client = get_client_for_user(admin)
        resp = client.get("/roles")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_non_admin_cannot_get_roles(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "usergetr", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.get("/roles")
        assert resp.status_code == 403

    def test_get_roles_returns_created_roles(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "adminlistr", "pass", admin_role)
        make_role(db, "editor")

        client = get_client_for_user(admin)
        resp = client.get("/roles")
        names = [r["name"] for r in resp.json()]
        assert "admin" in names
        assert "editor" in names


class TestUpdateRole:
    def test_admin_can_update_role(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "adminupdater", "pass", admin_role)
        role = make_role(db, "oldrole")

        client = get_client_for_user(admin)
        resp = client.put(f"/roles/{role.id}", json={"name": "newrole"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "newrole"

    def test_update_nonexistent_role(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "adminupdater2", "pass", admin_role)

        client = get_client_for_user(admin)
        resp = client.put("/roles/99999", json={"name": "x"})
        assert resp.status_code == 404

    def test_non_admin_cannot_update_role(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "userupdater", "pass", user_role)
        role = make_role(db, "somerole")

        client = get_client_for_user(user)
        resp = client.put(f"/roles/{role.id}", json={"name": "hacked"})
        assert resp.status_code == 403


class TestDeleteRole:
    def test_admin_can_delete_role(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admindelr", "pass", admin_role)
        role = make_role(db, "deleterole")

        client = get_client_for_user(admin)
        resp = client.delete(f"/roles/{role.id}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_delete_nonexistent_role(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "admindelr2", "pass", admin_role)

        client = get_client_for_user(admin)
        resp = client.delete("/roles/99999")
        assert resp.status_code == 404

    def test_non_admin_cannot_delete_role(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "userdelr", "pass", user_role)
        role = make_role(db, "protectedrole")

        client = get_client_for_user(user)
        resp = client.delete(f"/roles/{role.id}")
        assert resp.status_code == 403
