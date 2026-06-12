import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class UploadType(str, enum.Enum):
    PURCHASE_REGISTER = "PURCHASE_REGISTER"
    GSTR2B = "GSTR2B"


class UploadStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_type = Column(SAEnum(UploadType), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=True)
    period = Column(String(6), nullable=True)  # MMYYYY
    status = Column(SAEnum(UploadStatus), nullable=False, default=UploadStatus.PENDING)
    error_message = Column(String(1024), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    client = relationship("Client", back_populates="uploads")
    uploader = relationship("User", back_populates="uploads")
    column_mapping = relationship("ColumnMapping", back_populates="upload", uselist=False)
    purchase_invoices = relationship("PurchaseInvoice", back_populates="upload")
    gstr2b_invoices = relationship("Gstr2bInvoice", back_populates="upload")


class ColumnMapping(Base):
    __tablename__ = "column_mappings"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False, unique=True)
    mapping = Column(JSON, nullable=False)  # {"canonical_field": "source_column"}
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    upload = relationship("Upload", back_populates="column_mapping")
