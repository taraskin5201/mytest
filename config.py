from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
ALGORITHM = os.getenv("ALGORITHM")

class Settings(BaseSettings):
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
    SECRET_KEY: str = "SUPER_SECRET_KEY"
    ALGORITHM: str = "ALGORITHM"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

settings = Settings()