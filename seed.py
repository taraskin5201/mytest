from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db import SessionLocal, Base, engine
import models
from auth import hash_password

# --- Початкові дані ---
ROLES = ["admin", "editor", "user"]

USERS = [
    {"username": "admin1", "password": "adminpass", "role": "admin"},
    {"username": "editor1", "password": "editorpass", "role": "editor"},
    {"username": "user1", "password": "userpass", "role": "user"},
    {"username": "user2", "password": "userpass", "role": "user"}
]

ARTICLES = [
    {"title": "Welcome Article", "content": "This is the first article."},
    {"title": "Editor Tips", "content": "How to manage articles."},
    {"title": "User Guide", "content": "Guide for users."}
]


def seed():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # --- Створюємо ролі ---
        existing_roles = {r.name: r for r in db.query(models.Role).all()}
        for role_name in ROLES:
            if role_name not in existing_roles:
                role = models.Role(name=role_name)
                db.add(role)
        db.commit()
        roles = {r.name: r for r in db.query(models.Role).all()}
        print(f"Roles created: {', '.join(roles.keys())}")

        # --- Створюємо користувачів ---
        existing_users = {u.username: u for u in db.query(models.User).all()}
        for u in USERS:
            if u["username"] not in existing_users:
                user = models.User(
                    username=u["username"],
                    hashed_password = hash_password(u["password"]),
                    role_id=roles[u["role"]].id
                )
                db.add(user)
        db.commit()
        users = {u.username: u for u in db.query(models.User).all()}
        print(f"Users created: {', '.join(users.keys())}")

        # --- Створюємо статті ---
        existing_articles = db.query(models.Article).all()
        if not existing_articles:
            for i, art in enumerate(ARTICLES):
                owner_username = list(users.keys())[i % len(users)]
                article = models.Article(
                    title=art["title"],
                    content=art["content"],
                    owner_id=users[owner_username].id
                )
                db.add(article)
            db.commit()
            print(f"{len(ARTICLES)} articles created.")
        else:
            print("Articles already exist, skipping.")

        print("Database seeding complete")

    except IntegrityError as e:
        db.rollback()
        print("Error seeding database:", e)
    finally:
        db.close()


if __name__ == "__main__":
    seed()