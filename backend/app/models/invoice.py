from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Numeric, Index
from sqlalchemy.orm import relationship
from app.database import Base


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("reconciliation_runs.id"), nullable=True, index=True)

    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=True)
    supplier_gstin = Column(String(15), nullable=True)
    supplier_name = Column(String(255), nullable=True)
    taxable_amount = Column(Numeric(15, 2), nullable=True)
    igst = Column(Numeric(15, 2), nullable=True, default=Decimal("0"))
    cgst = Column(Numeric(15, 2), nullable=True, default=Decimal("0"))
    sgst = Column(Numeric(15, 2), nullable=True, default=Decimal("0"))
    total_tax = Column(Numeric(15, 2), nullable=True)
    invoice_type = Column(String(20), nullable=True)
    place_of_supply = Column(String(5), nullable=True)
    reverse_charge = Column(String(1), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    upload = relationship("Upload", back_populates="purchase_invoices")

    __table_args__ = (
        Index("ix_purchase_invoices_gstin_inv", "supplier_gstin", "invoice_number"),
    )


class Gstr2bInvoice(Base):
    __tablename__ = "gstr2b_invoices"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("reconciliation_runs.id"), nullable=True, index=True)

    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=True)
    supplier_gstin = Column(String(15), nullable=True)
    supplier_name = Column(String(255), nullable=True)
    taxable_amount = Column(Numeric(15, 2), nullable=True)
    igst = Column(Numeric(15, 2), nullable=True, default=Decimal("0"))
    cgst = Column(Numeric(15, 2), nullable=True, default=Decimal("0"))
    sgst = Column(Numeric(15, 2), nullable=True, default=Decimal("0"))
    total_tax = Column(Numeric(15, 2), nullable=True)
    invoice_type = Column(String(20), nullable=True)
    place_of_supply = Column(String(5), nullable=True)
    itc_availability = Column(String(10), nullable=True)
    reason = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    upload = relationship("Upload", back_populates="gstr2b_invoices")

    __table_args__ = (
        Index("ix_gstr2b_invoices_gstin_inv", "supplier_gstin", "invoice_number"),
    )
