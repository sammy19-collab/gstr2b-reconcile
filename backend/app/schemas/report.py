from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime


class VendorAnalyticsOut(BaseModel):
    id: int
    run_id: int
    supplier_gstin: Optional[str] = None
    supplier_name: Optional[str] = None
    total_invoices: int
    matched: int
    missing_in_2b: int
    missing_in_books: int
    tax_mismatch: int
    itc_available: Decimal
    itc_at_risk: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}
