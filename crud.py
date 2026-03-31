from sqlalchemy.orm import Session
from models import User, Article, Role
from auth import hash_password
from schemas import UserUpdate, RoleUpdate


# --- USERS ---
def create_user(db: Session, user):
    db_user = User(
        username=user.username,
        hashed_password=hash_password(user.password),
        role_id=user.role_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db, search="", offset=0, limit=10):
    q = db.query(User)
    if search:
        q = q.filter(User.username.ilike(f"%{search}%"))
    return q.offset(offset).limit(limit).all()

def update_user(db: Session, user_id: int, data: UserUpdate):
    user = db.query(User).get(user_id)
    if not user:
        return None
    for k, v in data.dict(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(User).get(user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

# --- ROLES ---
def create_role(db, role):
    db_role = Role(**role.dict())
    db.add(db_role)
    db.commit()
    return db_role

def get_roles(db: Session):
    return db.query(Role).all()

def update_role(db: Session, role_id: int, data: RoleUpdate):
    role = db.query(Role).get(role_id)
    if not role:
        return None
    for k, v in data.dict(exclude_unset=True).items():
        setattr(role, k, v)
    db.commit()
    db.refresh(role)
    return role

def delete_role(db: Session, role_id: int):
    role = db.query(Role).get(role_id)
    if not role:
        return False
    db.delete(role)
    db.commit()
    return True

# --- ARTICLES ---
def create_article(db, article, user_id):
    db_article = Article(**article.dict(), owner_id=user_id)
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

def get_articles(db, search="", offset=0, limit=10):
    q = db.query(Article)
    if search:
        q = q.filter(
            Article.title.ilike(f"%{search}%") |
            Article.content.ilike(f"%{search}%")
        )
    return q.offset(offset).limit(limit).all()