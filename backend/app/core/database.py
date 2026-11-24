from app.core.config import settings
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Основная БД
engine: Engine = create_engine(
    settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=300
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
