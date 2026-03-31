from pydantic import BaseModel
from typing import Optional

# --- Role ---
class RoleCreate(BaseModel):
    name: str

class RoleOut(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }

class RoleUpdate(BaseModel):
    name: Optional[str]

# --- User ---
class UserCreate(BaseModel):
    username: str
    password: str
    role_id: int

class UserUpdate(BaseModel):
    username: Optional[str]
    role_id: Optional[int]

class UserOut(BaseModel):
    id: int
    username: str
    role: RoleOut

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    username: Optional[str]
    role_id: Optional[int]

# --- Article ---
class ArticleCreate(BaseModel):
    title: str
    content: str

class ArticleUpdate(BaseModel):
    title: Optional[str]
    content: Optional[str]

class ArticleOut(BaseModel):
    id: int
    title: str
    content: str
    owner: UserOut

    model_config = {
        "from_attributes": True
    }