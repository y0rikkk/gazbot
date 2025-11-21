"""Database configuration and session management."""

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Create engine (синхронный)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, echo=False)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """Dependency для получения database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
