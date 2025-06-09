from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

DATABASE_URL = 'sqlite:///filemaster.db'
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ClientRequest(Base):
    __tablename__ = 'client_request'

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)
    modules = relationship("Module", back_populates="request")

class Module(Base):
    __tablename__ = 'module'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('client_request.id'), nullable=False)
    kind = Column(String(50))
    description = Column(String(255))
    completed = Column(Boolean, default=False)
    result_data = Column(JSON, nullable=True)
    file_path = Column(String(255))
    answer = Column(String)

    request = relationship("ClientRequest", back_populates="modules")

    def update_results(self, data: dict):
        if self.result_data is None:
            self.result_data = {}
        self.result_data.update(data)

class AccessLog(Base):
    __tablename__ = 'access_log'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('client_request.id'), nullable=False)
    module_id = Column(Integer, ForeignKey('module.id'), nullable=True)
    ip_address = Column(String(64))
    action = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)
