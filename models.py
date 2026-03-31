from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from db import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role")
    articles = relationship("Article", back_populates="owner")

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    content = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="articles")