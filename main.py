from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import Base, engine
from deps import get_db, get_current_user
import crud, models, schemas, auth
from permissions import *

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ================= AUTH =================
from fastapi.security import OAuth2PasswordRequestForm


@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(400, "Invalid credentials")
    token = auth.create_token({"sub": user.username})
    return {"access_token": token}


# ================= USERS =================
@app.get("/users", response_model=list[schemas.UserOut])
def users(q: str = "", offset: int = 0, limit: int = 10,
          db: Session = Depends(get_db),
          current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403)
    return crud.get_users(db, q, offset, limit)


@app.post("/users")
def create_user(user: schemas.UserCreate,
                db: Session = Depends(get_db),
                current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403)
    return crud.create_user(db, user)


@app.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user_endpoint(user_id: int,
                         data: schemas.UserUpdate,
                         db: Session = Depends(get_db),
                         current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    updated = crud.update_user(db, user_id, data)
    if not updated:
        raise HTTPException(404, "User not found")
    return updated

@app.delete("/users/{user_id}")
def delete_user_endpoint(user_id: int,
                         db: Session = Depends(get_db),
                         current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    deleted = crud.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(404, "User not found")
    return {"ok": True}


# ================= ROLES =================
@app.post("/roles")
def create_role(role: schemas.RoleCreate,
                db: Session = Depends(get_db),
                current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403)
    return crud.create_role(db, role)


@app.get("/roles", response_model=list[schemas.RoleOut])
def get_roles_endpoint(db: Session = Depends(get_db),
                       current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    return crud.get_roles(db)

@app.put("/roles/{role_id}", response_model=schemas.RoleOut)
def update_role_endpoint(role_id: int,
                         data: schemas.RoleUpdate,
                         db: Session = Depends(get_db),
                         current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    updated = crud.update_role(db, role_id, data)
    if not updated:
        raise HTTPException(404, "Role not found")
    return updated

@app.delete("/roles/{role_id}")
def delete_role_endpoint(role_id: int,
                         db: Session = Depends(get_db),
                         current=Depends(get_current_user)):
    if not is_admin(current):
        raise HTTPException(403, "Admin only")
    deleted = crud.delete_role(db, role_id)
    if not deleted:
        raise HTTPException(404, "Role not found")
    return {"ok": True}


# ================= ARTICLES =================
@app.post("/articles", response_model=schemas.ArticleOut)
def create_article(article: schemas.ArticleCreate,
                   db: Session = Depends(get_db),
                   current=Depends(get_current_user)):
    return crud.create_article(db, article, current.id)


@app.get("/articles", response_model=list[schemas.ArticleOut])
def articles(q: str = "", offset: int = 0, limit: int = 10,
             db: Session = Depends(get_db),
             current=Depends(get_current_user)):
    return crud.get_articles(db, q, offset, limit)


@app.get("/articles/{id}", response_model=schemas.ArticleOut)
def get_article(id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    article = db.query(models.Article).get(id)
    if not article:
        raise HTTPException(404)
    return article


@app.put("/articles/{id}")
def update_article(id: int,
                   data: schemas.ArticleUpdate,
                   db: Session = Depends(get_db),
                   current=Depends(get_current_user)):
    article = db.query(models.Article).get(id)
    if not article:
        raise HTTPException(404)

    if not can_edit_article(current, article):
        raise HTTPException(403)

    for k, v in data.dict(exclude_unset=True).items():
        setattr(article, k, v)

    db.commit()
    return article


@app.delete("/articles/{id}")
def delete_article(id: int,
                   db: Session = Depends(get_db),
                   current=Depends(get_current_user)):
    article = db.query(models.Article).get(id)

    if not article:
        raise HTTPException(404)

    if not can_delete_article(current, article):
        raise HTTPException(403)

    db.delete(article)
    db.commit()
    return {"ok": True}