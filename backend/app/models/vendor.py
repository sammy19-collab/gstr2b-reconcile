from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from app.database import Base


class VendorAnalytics(Base):
    __tablename__ = "vendor_analytics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("reconciliation_runs.id"), nullable=False, index=True)
    supplier_gstin = Column(String(15), nullable=True)
    supplier_name = Column(String(255), nullable=True)
    total_invoices = Column(Integer, nullable=False, default=0)
    matched = Column(Integer, nullable=False, default=0)
    missing_in_2b = Column(Integer, nullable=False, default=0)
    missing_in_books = Column(Integer, nullable=False, default=0)
    tax_mismatch = Column(Integer, nullable=False, default=0)
    itc_available = Column(Numeric(15, 2), nullable=False, default=0)
    itc_at_risk = Column(Numeric(15, 2), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
