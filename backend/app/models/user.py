import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.USER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    clients = relationship("Client", back_populates="owner")
    uploads = relationship("Upload", back_populates="uploader")
    audit_logs = relationship("AuditLog", back_populates="user")
