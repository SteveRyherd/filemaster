"""Database configuration utilities."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import Base
from ..settings import Settings

engine = create_engine(Settings().DATABASE_URL, future=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
