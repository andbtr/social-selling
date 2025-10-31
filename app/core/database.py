from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings

# Detectar si estamos usando SQLite o Postgres (u otro)
is_sqlite = settings.database_url.startswith("sqlite")

# Crear el engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True,  # importante para conexiones vivas en RDS/Postgres
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base declarativa
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Creates tables if they don't exist (useful the first time on a new DB)."""
    Base.metadata.create_all(bind=engine)
