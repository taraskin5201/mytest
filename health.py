from sqlalchemy import text
from sqlalchemy.orm import Session


def check_database(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}