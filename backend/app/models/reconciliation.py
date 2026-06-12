import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.database import Base


class RunStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MatchCategory(str, enum.Enum):
    EXACT_MATCH = "EXACT_MATCH"
    FUZZY_MATCH = "FUZZY_MATCH"
    TAX_MISMATCH = "TAX_MISMATCH"
    INVOICE_MISMATCH = "INVOICE_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    MISSING_IN_2B = "MISSING_IN_2B"
    MISSING_IN_BOOKS = "MISSING_IN_BOOKS"
    DUPLICATE = "DUPLICATE"


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    period = Column(String(6), nullable=False)  # MMYYYY
    pr_upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    g2b_upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    tax_tolerance = Column(Numeric(10, 2), nullable=False, default=Decimal("1.00"))
    fuzzy_threshold = Column(Integer, nullable=False, default=80)
    status = Column(SAEnum(RunStatus), nullable=False, default=RunStatus.QUEUED)
    summary = Column(JSON, nullable=True)
    error_message = Column(String(1024), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="reconciliation_runs")
    results = relationship("ReconciliationResult", back_populates="run")


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("reconciliation_runs.id"), nullable=False, index=True)
    category = Column(SAEnum(MatchCategory), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=True)
    purchase_invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=True)
    gstr2b_invoice_id = Column(Integer, ForeignKey("gstr2b_invoices.id"), nullable=True)
    purchase_data = Column(JSON, nullable=True)
    gstr2b_data = Column(JSON, nullable=True)
    tax_delta = Column(Numeric(15, 2), nullable=True)
    date_delta_days = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    run = relationship("ReconciliationRun", back_populates="results")
