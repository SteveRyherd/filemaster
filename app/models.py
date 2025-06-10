"""Database models for FileMaster."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """Application user."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    requests = relationship("ClientRequest", back_populates="creator")


class ClientRequest(Base):
    """Main request entity."""

    __tablename__ = "client_request"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    nickname = Column(String(128))
    creator_id = Column(Integer, ForeignKey("user.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="requests")
