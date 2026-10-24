from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


# Основная БД
engine: Engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print("[db] ", SessionLocal)
Base = declarative_base()
print("[db] ", Base)

# БД для аутентификации (Auth)
# auth_engine: Engine = create_engine(settings.AUTH_DATABASE_URL)
# AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)
# AuthBase = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# def get_auth_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
