from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db import Base, engine
from deps import get_db, get_current_user
import crud, models, schemas, auth
from permissions import is_admin, can_edit_article, can_delete_article
from schemas import (
    UserOut, UserCreate, UserUpdate,
    RoleOut, RoleCreate, RoleUpdate,
    ArticleOut, ArticleCreate, ArticleUpdate,
    TokenOut, DeleteResponse, ErrorResponse
)

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# Метаінформація та теги
# ─────────────────────────────────────────────
tags_metadata = [
    {
        "name": "Auth",
        "description": "Автентифікація користувачів. Отримання JWT-токена через логін.",
    },
    {
        "name": "Users",
        "description": (
            "Управління користувачами. "
            "Доступно лише адміністраторам. "
            "Підтримує пошук, пагінацію, оновлення та видалення."
        ),
    },
    {
        "name": "Roles",
        "description": (
            "Управління ролями користувачів. "
            "Доступно лише адміністраторам. "
            "Ролі визначають рівень доступу: `admin`, `editor`, `user`."
        ),
    },
    {
        "name": "Articles",
        "description": (
            "Управління статтями. "
            "Будь-який автентифікований користувач може створити статтю. "
            "Редагування — власник, editor або admin. "
            "Видалення — власник або admin."
        ),
    },
]

app = FastAPI(
    title="Articles API",
    description=(
        "REST API для управління статтями з рольовою моделлю доступу.\n\n"
        "## Ролі\n"
        "- **admin** — повний доступ до всіх ресурсів\n"
        "- **editor** — може редагувати будь-яку статтю\n"
        "- **user** — може створювати статті та редагувати/видаляти власні\n\n"
        "## Авторизація\n"
        "Використовується **JWT Bearer Token**. "
        "Отримайте токен через `POST /auth/login`, "
        "після чого передавайте його у заголовку `Authorization: Bearer <token>`."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

_errors = {
    401: {"model": ErrorResponse, "description": "Не автентифікований або невалідний токен"},
    403: {"model": ErrorResponse, "description": "Недостатньо прав доступу"},
    404: {"model": ErrorResponse, "description": "Ресурс не знайдено"},
}


# ═══════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════

@app.post(
    "/auth/login",
    tags=["Auth"],
    response_model=TokenOut,
    summary="Вхід у систему",
    description=(
        "Автентифікація користувача за логіном та паролем. "
        "Повертає **JWT access token**, який потрібно передавати "
        "у заголовку `Authorization: Bearer <token>` для всіх захищених ендпоінтів."
    ),
    responses={
        200: {"description": "Успішний вхід, токен повернуто"},
        400: {"model": ErrorResponse, "description": "Невірний логін або пароль"},
    },
)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(400, "Invalid credentials")
    token = auth.create_token({"sub": user.username})
    return TokenOut(access_token=token)


# ═══════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════

@app.get(
    "/users",
    tags=["Users"],
    response_model=list[UserOut],
    summary="Список користувачів",
    description=(
        "Повертає список усіх користувачів з підтримкою **пошуку** та **пагінації**. "
        "Доступно лише для ролі `admin`."
    ),
    responses={
        200: {"description": "Список користувачів"},
        **{k: _errors[k] for k in [401, 403]},
    },
)
def get_users(
    q: str = "",
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """
    Параметри запиту:
    - **q**: пошук за іменем користувача (частковий збіг, регістронезалежний)
    - **offset**: зміщення для пагінації (за замовчуванням 0)
    - **limit**: максимальна кількість результатів (за замовчуванням 10)
    """
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    return crud.get_users(db, q, offset, limit)


@app.post(
    "/users",
    tags=["Users"],
    response_model=UserOut,
    summary="Створити користувача",
    description="Створює нового користувача із заданим іменем, паролем та роллю. Доступно лише для `admin`.",
    responses={
        200: {"description": "Користувача створено"},
        **{k: _errors[k] for k in [401, 403]},
    },
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    return crud.create_user(db, user)


@app.put(
    "/users/{user_id}",
    tags=["Users"],
    response_model=UserOut,
    summary="Оновити користувача",
    description="Оновлює ім'я або роль існуючого користувача. Доступно лише для `admin`.",
    responses={
        200: {"description": "Користувача оновлено"},
        **{k: _errors[k] for k in [401, 403, 404]},
    },
)
def update_user_endpoint(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    updated = crud.update_user(db, user_id, data)
    if not updated:
        raise HTTPException(404, "User not found")
    return updated


@app.delete(
    "/users/{user_id}",
    tags=["Users"],
    response_model=DeleteResponse,
    summary="Видалити користувача",
    description="Видаляє користувача за його ID. Доступно лише для `admin`.",
    responses={
        200: {"description": "Користувача видалено"},
        **{k: _errors[k] for k in [401, 403, 404]},
    },
)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    if not crud.delete_user(db, user_id):
        raise HTTPException(404, "User not found")
    return DeleteResponse(ok=True)


# ═══════════════════════════════════════════════
# ROLES
# ═══════════════════════════════════════════════

@app.post(
    "/roles",
    tags=["Roles"],
    response_model=RoleOut,
    summary="Створити роль",
    description="Створює нову роль. Доступно лише для `admin`.",
    responses={
        200: {"description": "Роль створено"},
        **{k: _errors[k] for k in [401, 403]},
    },
)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    return crud.create_role(db, role)


@app.get(
    "/roles",
    tags=["Roles"],
    response_model=list[RoleOut],
    summary="Список ролей",
    description="Повертає всі існуючі ролі. Доступно лише для `admin`.",
    responses={
        200: {"description": "Список ролей"},
        **{k: _errors[k] for k in [401, 403]},
    },
)
def get_roles_endpoint(
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    return crud.get_roles(db)


@app.put(
    "/roles/{role_id}",
    tags=["Roles"],
    response_model=RoleOut,
    summary="Оновити роль",
    description="Змінює назву ролі за її ID. Доступно лише для `admin`.",
    responses={
        200: {"description": "Роль оновлено"},
        **{k: _errors[k] for k in [401, 403, 404]},
    },
)
def update_role_endpoint(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    updated = crud.update_role(db, role_id, data)
    if not updated:
        raise HTTPException(404, "Role not found")
    return updated


@app.delete(
    "/roles/{role_id}",
    tags=["Roles"],
    response_model=DeleteResponse,
    summary="Видалити роль",
    description="Видаляє роль за її ID. Доступно лише для `admin`.",
    responses={
        200: {"description": "Роль видалено"},
        **{k: _errors[k] for k in [401, 403, 404]},
    },
)
def delete_role_endpoint(
    role_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    if not crud.delete_role(db, role_id):
        raise HTTPException(404, "Role not found")
    return DeleteResponse(ok=True)


# ═══════════════════════════════════════════════
# ARTICLES
# ═══════════════════════════════════════════════

@app.post(
    "/articles",
    tags=["Articles"],
    response_model=ArticleOut,
    summary="Створити статтю",
    description="Створює нову статтю. Автором автоматично стає поточний авторизований користувач.",
    responses={
        200: {"description": "Статтю створено"},
        401: _errors[401],
    },
)
def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    return crud.create_article(db, article, current.id)


@app.get(
    "/articles",
    tags=["Articles"],
    response_model=list[ArticleOut],
    summary="Список статей",
    description=(
        "Повертає список статей з підтримкою **пошуку** (за заголовком та вмістом) "
        "та **пагінації**. Доступно для будь-якого авторизованого користувача."
    ),
    responses={
        200: {"description": "Список статей"},
        401: _errors[401],
    },
)
def get_articles(
    q: str = "",
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """
    Параметри запиту:
    - **q**: пошук за заголовком або вмістом (частковий збіг)
    - **offset**: зміщення для пагінації
    - **limit**: кількість результатів на сторінку
    """
    return crud.get_articles(db, q, offset, limit)


@app.get(
    "/articles/{id}",
    tags=["Articles"],
    response_model=ArticleOut,
    summary="Отримати статтю",
    description="Повертає одну статтю за її ID разом з інформацією про автора.",
    responses={
        200: {"description": "Дані статті"},
        **{k: _errors[k] for k in [401, 404]},
    },
)
def get_article(
    id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    article = db.query(models.Article).get(id)
    if not article:
        raise HTTPException(404, "Article not found")
    return article


@app.put(
    "/articles/{id}",
    tags=["Articles"],
    response_model=ArticleOut,
    summary="Оновити статтю",
    description=(
        "Оновлює заголовок та/або вміст статті. "
        "Дозволено: **власник** статті, **editor** або **admin**."
    ),
    responses={
        200: {"description": "Статтю оновлено"},
        **{k: _errors[k] for k in [401, 403, 404]},
    },
)
def update_article(
    id: int,
    data: ArticleUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    article = db.query(models.Article).get(id)
    if not article:
        raise HTTPException(404, "Article not found")
    if not can_edit_article(current, article):
        raise HTTPException(403, "Not allowed to edit this article")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(article, k, v)
    db.commit()
    db.refresh(article)
    return article


@app.delete(
    "/articles/{id}",
    tags=["Articles"],
    response_model=DeleteResponse,
    summary="Видалити статтю",
    description=(
        "Видаляє статтю за ID. "
        "Дозволено: **власник** статті або **admin**. "
        "Редактори (`editor`) не можуть видаляти чужі статті."
    ),
    responses={
        200: {"description": "Статтю видалено"},
        **{k: _errors[k] for k in [401, 403, 404]},
    },
)
def delete_article(
    id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    article = db.query(models.Article).get(id)
    if not article:
        raise HTTPException(404, "Article not found")
    if not can_delete_article(current, article):
        raise HTTPException(403, "Not allowed to delete this article")
    db.delete(article)
    db.commit()
    return DeleteResponse(ok=True)