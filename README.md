# Articles API

REST API для управління статтями з рольовою моделлю доступу. Побудовано на **FastAPI** + **PostgreSQL** + **SQLAlchemy**.

## Зміст

- [Технології](#технології)
- [Ролі та права доступу](#ролі-та-права-доступу)
- [Структура проєкту](#структура-проєкту)
- [Запуск через Docker](#запуск-через-docker)
- [Запуск локально](#запуск-локально)
- [Початкові дані (Seed)](#початкові-дані-seed)
- [Запуск тестів](#запуск-тестів)
- [Документація API](#документація-api)
- [Postman колекція](#postman-колекція)
- [Змінні середовища](#змінні-середовища)

---

## Технології

- **Python 3.13**
- **FastAPI** — веб-фреймворк
- **SQLAlchemy** — ORM
- **PostgreSQL 16** — база даних
- **Pydantic v2** — валідація даних
- **Argon2** — хешування паролів
- **JWT (HS256)** — авторизація
- **Docker + Docker Compose** — контейнеризація
- **pytest + pytest-cov** — тестування

---

## Ролі та права доступу

| Дія | user | editor | admin |
|-----|------|--------|-------|
| Переглядати статті | + | + | + |
| Створювати статті | + | + | + |
| Редагувати власні статті | + | + | + |
| Редагувати чужі статті | - | + | + |
| Видаляти власні статті | + | - | + |
| Видаляти чужі статті | - | - | + |
| Управління користувачами | - | - | + |
| Управління ролями | - | - | + |

---

## Структура проєкту

\`\`\`

    project/
    ├── main.py                 # Ендпоінти FastAPI
    ├── auth.py                 # Хешування паролів, JWT токени
    ├── config.py               # Налаштування (читає .env)
    ├── crud.py                 # Операції з базою даних
    ├── db.py                   # Підключення до БД, Base
    ├── deps.py                 # Залежності FastAPI (get_db, get_current_user)
    ├── models.py               # SQLAlchemy моделі (User, Role, Article)
    ├── permissions.py          # Перевірка прав доступу
    ├── schemas.py              # Pydantic схеми
    ├── seed.py                 # Наповнення БД початковими даними
    ├── health.py               # Перевірка стану сервісу та його залежностей
    ├── Dockerfile              # Образ для app та seed
    ├── Dockerfile.test         # Образ для тестів
    ├── docker-compose.yml      # Dev оточення
    ├── docker-compose.test.yml # Тестове оточення
    ├── requirements.txt        # Залежності проєкту
    ├── .env.example            # Шаблон змінних середовища
    ├── conftest.py         # Фікстури, SQLite in-memory
    ├── test_auth.py        # Тести авторизації
    ├── test_users.py       # Тести ендпоінтів /users
    ├── test_roles.py       # Тести ендпоінтів /roles
    ├── test_articles.py    # Тести ендпоінтів /articles
    └── test_unit.py        # Юніт-тести auth, permissions, crud
\`\`\`

---

## Запуск через Docker

### Вимоги

- [Docker Engine](https://docs.docker.com/engine/install/) 24+
- Docker Compose v2+

### Кроки

**1. Створи `.env` файл:**

\`\`\`bash
cp .env.example .env
\`\`\`

**2. Збери і запусти контейнери:**

\`\`\`bash
docker compose up --build
\`\`\`

Після запуску сервер доступний на \`http://localhost:8000\`.

**Запуск у фоні:**

\`\`\`bash
docker compose up -d --build
\`\`\`

**Зупинка:**

\`\`\`bash
docker compose down
\`\`\`

**Зупинка з видаленням даних БД:**

\`\`\`bash
docker compose down -v
\`\`\`

---

## Запуск локально

### Вимоги

- Python 3.11+
- PostgreSQL (або SQLite для швидкого старту)

### Кроки

**1. Встанови залежності:**

\`\`\`bash
pip install -r requirements.txt
\`\`\`

**2. Налаштуй підключення до БД.**

Для PostgreSQL — створи `.env` файл:

\`\`\`bash
cp .env.example .env
# Відредагуй DATABASE_URL у .env
\`\`\`

Для швидкого старту без PostgreSQL — заміни в `config.py`:

\`\`\`python
DATABASE_URL: str = "sqlite:///./dev.db"
\`\`\`

**3. Запусти сервер:**

\`\`\`bash
uvicorn main:app --reload
\`\`\`

Сервер запуститься на \`http://localhost:8000\`.

---

## Початкові дані (Seed)

Seed створює тестових користувачів і статті для роботи з API.

### Через Docker

Seed запускається **автоматично** при першому \`docker compose up\`.

Якщо потрібно запустити повторно:

\`\`\`bash
docker compose run --rm seed
\`\`\`

### Локально

\`\`\`bash
python seed.py
\`\`\`

### Що створює seed

**Ролі:**

| Назва |
|-------|
| admin |
| editor |
| user |

**Користувачі:**

| Username | Password | Роль |
|----------|----------|------|
| admin1 | adminpass | admin |
| editor1 | editorpass | editor |
| user1 | userpass | user |
| user2 | userpass | user |

**Статті:** 3 тестові статті з різними авторами.

---

## Запуск тестів

Тести використовують **SQLite in-memory** — PostgreSQL не потрібен.


### Локально

**1. Встанови тестові залежності:**

\`\`\`bash
pip install pytest pytest-cov httpx
\`\`\`

**2. Запусти тести:**

\`\`\`bash
pytest
\`\`\`

**3. Запусти з покриттям:**

\`\`\`bash
pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing
\`\`\`


### Що покривають тести

| Файл | Що тестується |
|------|--------------|
| \`test_auth.py\` | POST /auth/login |
| \`test_users.py\` | GET, POST, PUT, DELETE /users |
| \`test_roles.py\` | GET, POST, PUT, DELETE /roles |
| \`test_articles.py\` | GET, POST, PUT, DELETE /articles |
| \`test_unit.py\` | auth.py, permissions.py, crud.py |

Загальне покриття коду — **80%+**.

---

## Документація API

Після запуску сервера документація доступна за адресами:

| URL | Опис |
|-----|------|
| http://localhost:8000/docs | Swagger UI — інтерактивна документація |
| http://localhost:8000/redoc | ReDoc — альтернативний вигляд |
| http://localhost:8000/openapi.json | Сирий OpenAPI JSON |

### Авторизація в Swagger UI

1. Відкрий \`http://localhost:8000/docs\`
2. Виконай \`POST /auth/login\` (username: \`admin1\`, password: \`adminpass\`)
3. Натисни кнопку **Authorize** 


---

## Postman колекція

У репозиторії є колекція:

| Файл | Опис |
|---|-----|
| \`Articles_API_Auth_Users.postman_collection.json\` | Тільки Auth та Users (5 запитів) |

### Імпорт у Postman

1. Відкрий Postman
2. **Import** → перетягни \`.json\` файл
3. Запусти **Login** першим — токен збережеться автоматично у змінну \`{{token}}\`
4. Далі запускай будь-які запити або використовуй **Collection Runner**

---

## Змінні середовища

Всі змінні зберігаються у файлі \`.env\` .

| Змінна | За замовчуванням | Опис |
|--------|-----------------|------|
| \`POSTGRES_USER\` | \`postgres\` | Юзер PostgreSQL |
| \`POSTGRES_PASSWORD\` | \`postgres\` | Пароль PostgreSQL |
| \`POSTGRES_DB\` | \`mydb\` | Назва бази даних |
| \`SECRET_KEY\` | \`change_me_in_production\` | Секрет для підпису JWT |
| \`ALGORITHM\` | \`ALGORITHM\` | Алгоритм JWT |
| \`ACCESS_TOKEN_EXPIRE_MINUTES\` | \`60\` | Час дії токена у хвилинах |
