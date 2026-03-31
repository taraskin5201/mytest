from pydantic import BaseModel, Field
from typing import Optional


# --- Role ---
class RoleCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Унікальна назва ролі",
        examples=["editor"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "editor"}]
        }
    }


class RoleOut(BaseModel):
    id: int = Field(..., description="Унікальний ідентифікатор ролі", examples=[1])
    name: str = Field(..., description="Назва ролі", examples=["admin"])

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{"id": 1, "name": "admin"}]
        }
    }


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=50,
        description="Нова назва ролі",
        examples=["moderator"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "moderator"}]
        }
    }


# --- User ---
class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Унікальне ім'я користувача",
        examples=["john_doe"]
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Пароль користувача (мінімум 6 символів)",
        examples=["securepass123"]
    )
    role_id: int = Field(
        ...,
        description="ID ролі, яку отримає користувач",
        examples=[2]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"username": "john_doe", "password": "securepass123", "role_id": 2}]
        }
    }


class UserUpdate(BaseModel):
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        description="Нове ім'я користувача",
        examples=["john_updated"]
    )
    role_id: Optional[int] = Field(
        None,
        description="Новий ID ролі",
        examples=[3]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"username": "john_updated", "role_id": 3}]
        }
    }


class UserOut(BaseModel):
    id: int = Field(..., description="Унікальний ідентифікатор користувача", examples=[1])
    username: str = Field(..., description="Ім'я користувача", examples=["john_doe"])
    role: RoleOut = Field(..., description="Роль користувача")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "username": "john_doe",
                "role": {"id": 2, "name": "editor"}
            }]
        }
    }


# --- Token ---
class TokenOut(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Тип токена",
        examples=["bearer"]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }]
        }
    }


# --- Article ---
class ArticleCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Заголовок статті",
        examples=["Як налаштувати Docker"]
    )
    content: str = Field(
        ...,
        min_length=10,
        description="Вміст статті",
        examples=["Docker — це платформа для контейнеризації додатків..."]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "title": "Як налаштувати Docker",
                "content": "Docker — це платформа для контейнеризації додатків..."
            }]
        }
    }


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=200,
        description="Новий заголовок статті",
        examples=["Оновлений заголовок"]
    )
    content: Optional[str] = Field(
        None,
        min_length=10,
        description="Новий вміст статті",
        examples=["Оновлений вміст статті..."]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "title": "Оновлений заголовок",
                "content": "Оновлений вміст статті..."
            }]
        }
    }


class ArticleOut(BaseModel):
    id: int = Field(..., description="Унікальний ідентифікатор статті", examples=[1])
    title: str = Field(..., description="Заголовок статті", examples=["Як налаштувати Docker"])
    content: str = Field(..., description="Вміст статті", examples=["Docker — це платформа..."])
    owner: UserOut = Field(..., description="Автор статті")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "id": 1,
                "title": "Як налаштувати Docker",
                "content": "Docker — це платформа для контейнеризації...",
                "owner": {
                    "id": 2,
                    "username": "john_doe",
                    "role": {"id": 2, "name": "editor"}
                }
            }]
        }
    }


# --- Misc ---
class DeleteResponse(BaseModel):
    ok: bool = Field(..., description="Результат операції видалення", examples=[True])

    model_config = {
        "json_schema_extra": {"examples": [{"ok": True}]}
    }


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Опис помилки", examples=["User not found"])