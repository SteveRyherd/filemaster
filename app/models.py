"""Database models for FileMaster."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
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
    expires_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_accessed = Column(DateTime)
    meta = Column(JSON, default=dict)

    creator = relationship("User", back_populates="requests")
    modules = relationship(
        "Module", back_populates="request", cascade="all, delete-orphan"
    )
    access_logs = relationship(
        "AccessLog", back_populates="request", cascade="all, delete-orphan"
    )


class Module(Base):
    """Generic module instance."""

    __tablename__ = "module"

    id = Column(Integer, primary_key=True)
    request_id = Column(
        Integer,
        ForeignKey("client_request.id"),
        nullable=False,
    )
    kind = Column(String(50), nullable=False)
    label = Column(String(255))
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    required = Column(Boolean, default=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)

    result_data = Column(JSON, default=dict)
    config = Column(JSON, default=dict)
    allow_edit = Column(Boolean, default=False)
    show_previous = Column(Boolean, default=True)
    expires_at = Column(DateTime)

    version = Column(Integer, default=1)
    edit_history = Column(JSON, default=list)

    request = relationship("ClientRequest", back_populates="modules")
    access_logs = relationship("AccessLog", back_populates="module")


class AccessLog(Base):
    """Security and analytics logging."""

    __tablename__ = "access_log"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("client_request.id"))
    module_id = Column(Integer, ForeignKey("module.id"), nullable=True)
    ip_address = Column(String(64))
    user_agent = Column(String(255))
    action = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

    request = relationship("ClientRequest", back_populates="access_logs")
    module = relationship("Module", back_populates="access_logs")
