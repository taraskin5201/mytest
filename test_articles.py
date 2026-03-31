import pytest
from conftest import (
    make_role, make_user, make_article, get_client_for_user,
    TestingSessionLocal
)


@pytest.fixture
def db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


# ===================== ARTICLES TESTS =====================

class TestCreateArticle:
    def test_any_user_can_create_article(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "articleuser", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.post("/articles", json={
            "title": "My Article",
            "content": "Hello World"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "My Article"
        assert data["owner"]["username"] == "articleuser"

    def test_admin_can_create_article(self, db):
        admin_role = make_role(db, "admin")
        admin = make_user(db, "adminarticle", "pass", admin_role)

        client = get_client_for_user(admin)
        resp = client.post("/articles", json={
            "title": "Admin Article",
            "content": "Admin content"
        })
        assert resp.status_code == 200


class TestGetArticles:
    def test_get_articles_list(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "listuser", "pass", user_role)
        make_article(db, user, "Article 1")
        make_article(db, user, "Article 2")

        client = get_client_for_user(user)
        resp = client.get("/articles")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_articles_with_search(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "searchuser", "pass", user_role)
        make_article(db, user, "Unique Title ABC", "content")
        make_article(db, user, "Other Title", "content")

        client = get_client_for_user(user)
        resp = client.get("/articles?q=Unique")
        assert resp.status_code == 200
        data = resp.json()
        assert all("unique" in a["title"].lower() for a in data)

    def test_get_articles_pagination(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "paguser", "pass", user_role)
        for i in range(5):
            make_article(db, user, f"Article {i}")

        client = get_client_for_user(user)
        resp = client.get("/articles?limit=2&offset=0")
        assert resp.status_code == 200
        assert len(resp.json()) <= 2


class TestGetSingleArticle:
    def test_get_existing_article(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "getartuser", "pass", user_role)
        article = make_article(db, user, "Single Article")

        client = get_client_for_user(user)
        resp = client.get(f"/articles/{article.id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Single Article"

    def test_get_nonexistent_article(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "getartuser2", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.get("/articles/99999")
        assert resp.status_code == 404


class TestUpdateArticle:
    def test_owner_can_update_article(self, db):
        user_role = make_role(db, "user")
        owner = make_user(db, "owneruser", "pass", user_role)
        article = make_article(db, owner, "Original Title")

        client = get_client_for_user(owner)
        resp = client.put(f"/articles/{article.id}", json={"title": "Updated Title"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"

    def test_editor_can_update_any_article(self, db):
        user_role = make_role(db, "user")
        editor_role = make_role(db, "editor")
        owner = make_user(db, "owneruser2", "pass", user_role)
        editor = make_user(db, "editoruser", "pass", editor_role)
        article = make_article(db, owner, "Owner's Article")

        client = get_client_for_user(editor)
        resp = client.put(f"/articles/{article.id}", json={"title": "Editor Changed"})
        assert resp.status_code == 200

    def test_admin_can_update_any_article(self, db):
        admin_role = make_role(db, "admin")
        user_role = make_role(db, "user")
        admin = make_user(db, "adminupd2", "pass", admin_role)
        owner = make_user(db, "owneruser3", "pass", user_role)
        article = make_article(db, owner, "Owner's Article 2")

        client = get_client_for_user(admin)
        resp = client.put(f"/articles/{article.id}", json={"title": "Admin Changed"})
        assert resp.status_code == 200

    def test_other_user_cannot_update_article(self, db):
        user_role = make_role(db, "user")
        owner = make_user(db, "owneruser4", "pass", user_role)
        other = make_user(db, "otheruser", "pass", user_role)
        article = make_article(db, owner, "Protected Article")

        client = get_client_for_user(other)
        resp = client.put(f"/articles/{article.id}", json={"title": "Hacked"})
        assert resp.status_code == 403

    def test_update_nonexistent_article(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "userupd2", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.put("/articles/99999", json={"title": "x"})
        assert resp.status_code == 404


class TestDeleteArticle:
    def test_owner_can_delete_article(self, db):
        user_role = make_role(db, "user")
        owner = make_user(db, "delowner", "pass", user_role)
        article = make_article(db, owner, "To Delete")

        client = get_client_for_user(owner)
        resp = client.delete(f"/articles/{article.id}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_admin_can_delete_any_article(self, db):
        admin_role = make_role(db, "admin")
        user_role = make_role(db, "user")
        admin = make_user(db, "admindelart", "pass", admin_role)
        owner = make_user(db, "delowner2", "pass", user_role)
        article = make_article(db, owner, "Admin Deletes")

        client = get_client_for_user(admin)
        resp = client.delete(f"/articles/{article.id}")
        assert resp.status_code == 200

    def test_editor_cannot_delete_others_article(self, db):
        editor_role = make_role(db, "editor")
        user_role = make_role(db, "user")
        editor = make_user(db, "editorDel", "pass", editor_role)
        owner = make_user(db, "delowner3", "pass", user_role)
        article = make_article(db, owner, "Editor Cannot Delete")

        client = get_client_for_user(editor)
        resp = client.delete(f"/articles/{article.id}")
        assert resp.status_code == 403

    def test_other_user_cannot_delete_article(self, db):
        user_role = make_role(db, "user")
        owner = make_user(db, "delowner4", "pass", user_role)
        other = make_user(db, "otheruserdel", "pass", user_role)
        article = make_article(db, owner, "Protected Delete")

        client = get_client_for_user(other)
        resp = client.delete(f"/articles/{article.id}")
        assert resp.status_code == 403

    def test_delete_nonexistent_article(self, db):
        user_role = make_role(db, "user")
        user = make_user(db, "delnone", "pass", user_role)

        client = get_client_for_user(user)
        resp = client.delete("/articles/99999")
        assert resp.status_code == 404
