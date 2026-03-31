import pytest
from unittest.mock import MagicMock
from jose import JWTError

from auth import hash_password, verify_password, create_token, decode_token
from permissions import is_admin, is_editor, can_edit_article, can_delete_article
import crud
from schemas import UserCreate, UserUpdate, RoleCreate, RoleUpdate, ArticleCreate
from conftest import make_role, make_user, make_article, TestingSessionLocal


@pytest.fixture
def db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


# ===================== AUTH UNIT TESTS =====================

class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        h = hash_password("secret")
        assert isinstance(h, str)

    def test_hash_is_not_plaintext(self):
        h = hash_password("secret")
        assert h != "secret"

    def test_verify_correct_password(self):
        h = hash_password("mypassword")
        assert verify_password("mypassword", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("mypassword")
        assert verify_password("wrongpassword", h) is False

    def test_two_hashes_differ(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # argon2 uses random salt


class TestTokens:
    def test_create_and_decode_token(self):
        token = create_token({"sub": "testuser"})
        payload = decode_token(token)
        assert payload["sub"] == "testuser"

    def test_token_has_expiry(self):
        token = create_token({"sub": "user"})
        payload = decode_token(token)
        assert "exp" in payload

    def test_invalid_token_raises(self):
        with pytest.raises(Exception):
            decode_token("invalid.token.here")

    def test_tampered_token_raises(self):
        token = create_token({"sub": "user"})
        tampered = token + "tampered"
        with pytest.raises(Exception):
            decode_token(tampered)


# ===================== PERMISSIONS UNIT TESTS =====================

def make_mock_user(role_name):
    user = MagicMock()
    user.role.name = role_name
    user.id = 1
    return user


def make_mock_article(owner_id):
    article = MagicMock()
    article.owner_id = owner_id
    return article


class TestIsAdmin:
    def test_admin_is_admin(self):
        assert is_admin(make_mock_user("admin")) is True

    def test_editor_is_not_admin(self):
        assert is_admin(make_mock_user("editor")) is False

    def test_user_is_not_admin(self):
        assert is_admin(make_mock_user("user")) is False


class TestIsEditor:
    def test_editor_is_editor(self):
        assert is_editor(make_mock_user("editor")) is True

    def test_admin_is_not_editor(self):
        assert is_editor(make_mock_user("admin")) is False

    def test_user_is_not_editor(self):
        assert is_editor(make_mock_user("user")) is False


class TestCanEditArticle:
    def test_owner_can_edit(self):
        user = make_mock_user("user")
        user.id = 5
        article = make_mock_article(5)
        assert can_edit_article(user, article) is True

    def test_editor_can_edit(self):
        user = make_mock_user("editor")
        user.id = 2
        article = make_mock_article(99)
        assert can_edit_article(user, article) is True

    def test_admin_can_edit(self):
        user = make_mock_user("admin")
        user.id = 3
        article = make_mock_article(99)
        assert can_edit_article(user, article) is True

    def test_other_user_cannot_edit(self):
        user = make_mock_user("user")
        user.id = 10
        article = make_mock_article(99)
        assert can_edit_article(user, article) is False


class TestCanDeleteArticle:
    def test_owner_can_delete(self):
        user = make_mock_user("user")
        user.id = 5
        article = make_mock_article(5)
        assert can_delete_article(user, article) is True

    def test_admin_can_delete(self):
        user = make_mock_user("admin")
        user.id = 3
        article = make_mock_article(99)
        assert can_delete_article(user, article) is True

    def test_editor_cannot_delete_others(self):
        user = make_mock_user("editor")
        user.id = 10
        article = make_mock_article(99)
        assert can_delete_article(user, article) is False

    def test_regular_user_cannot_delete_others(self):
        user = make_mock_user("user")
        user.id = 10
        article = make_mock_article(99)
        assert can_delete_article(user, article) is False


# ===================== CRUD UNIT TESTS =====================

class TestCrudUsers:
    def test_create_user(self, db):
        role = make_role(db, "user")
        user_schema = UserCreate(username="cruduser", password="pass", role_id=role.id)
        user = crud.create_user(db, user_schema)
        assert user.id is not None
        assert user.username == "cruduser"

    def test_get_users(self, db):
        role = make_role(db, "user")
        make_user(db, "listuser1", "pass", role)
        make_user(db, "listuser2", "pass", role)
        users = crud.get_users(db)
        assert len(users) >= 2

    def test_get_users_with_search(self, db):
        role = make_role(db, "user")
        make_user(db, "findme", "pass", role)
        make_user(db, "dontfind", "pass", role)
        results = crud.get_users(db, search="findme")
        assert all("findme" in u.username for u in results)

    def test_update_user(self, db):
        role = make_role(db, "user")
        user = make_user(db, "updateme", "pass", role)
        updated = crud.update_user(db, user.id, UserUpdate(username="updated"))
        assert updated.username == "updated"

    def test_update_nonexistent_user(self, db):
        result = crud.update_user(db, 99999, UserUpdate(username="x"))
        assert result is None

    def test_delete_user(self, db):
        role = make_role(db, "user")
        user = make_user(db, "deleteme", "pass", role)
        result = crud.delete_user(db, user.id)
        assert result is True

    def test_delete_nonexistent_user(self, db):
        result = crud.delete_user(db, 99999)
        assert result is False


class TestCrudRoles:
    def test_create_role(self, db):
        role = crud.create_role(db, RoleCreate(name="testrole"))
        assert role.id is not None
        assert role.name == "testrole"

    def test_get_roles(self, db):
        make_role(db, "roleA")
        make_role(db, "roleB")
        roles = crud.get_roles(db)
        names = [r.name for r in roles]
        assert "roleA" in names
        assert "roleB" in names

    def test_update_role(self, db):
        role = make_role(db, "oldrole")
        updated = crud.update_role(db, role.id, RoleUpdate(name="newrole"))
        assert updated.name == "newrole"

    def test_update_nonexistent_role(self, db):
        result = crud.update_role(db, 99999, RoleUpdate(name="x"))
        assert result is None

    def test_delete_role(self, db):
        role = make_role(db, "todelrole")
        result = crud.delete_role(db, role.id)
        assert result is True

    def test_delete_nonexistent_role(self, db):
        result = crud.delete_role(db, 99999)
        assert result is False


class TestCrudArticles:
    def test_create_article(self, db):
        role = make_role(db, "user")
        user = make_user(db, "artcreator", "pass", role)
        schema = ArticleCreate(title="Title", content="Content")
        article = crud.create_article(db, schema, user.id)
        assert article.id is not None
        assert article.owner_id == user.id

    def test_get_articles(self, db):
        role = make_role(db, "user")
        user = make_user(db, "artlister", "pass", role)
        make_article(db, user, "Art A")
        make_article(db, user, "Art B")
        articles = crud.get_articles(db)
        assert len(articles) >= 2

    def test_get_articles_search_title(self, db):
        role = make_role(db, "user")
        user = make_user(db, "artsearcher", "pass", role)
        make_article(db, user, "UniqueTitle", "content")
        make_article(db, user, "Other", "content")
        results = crud.get_articles(db, search="UniqueTitle")
        assert all("uniquetitle" in a.title.lower() for a in results)

    def test_get_articles_search_content(self, db):
        role = make_role(db, "user")
        user = make_user(db, "artsearcher2", "pass", role)
        make_article(db, user, "Some Title", "UniqueContent123")
        results = crud.get_articles(db, search="UniqueContent123")
        assert len(results) >= 1
