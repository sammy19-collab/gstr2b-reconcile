from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), nullable=False)
    pan = Column(String(10), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owner = relationship("User", back_populates="clients")
    uploads = relationship("Upload", back_populates="client")
    reconciliation_runs = relationship("ReconciliationRun", back_populates="client")
