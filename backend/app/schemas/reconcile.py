from pydantic import BaseModel
from decimal import Decimal
from typing import Literal, Optional, List
from datetime import datetime


class ReconcileRunRequest(BaseModel):
    client_id: int
    period: str  # MMYYYY
    pr_upload_id: int
    g2b_upload_id: int
    tax_tolerance: Decimal = Decimal("1.00")
    fuzzy_threshold: int = 80


class RunSummary(BaseModel):
    total_invoices: int
    total_matched: int
    missing_in_2b: int
    missing_in_books: int
    tax_mismatch: int
    invoice_mismatch: int
    date_mismatch: int
    duplicates: int
    itc_available: Decimal
    itc_at_risk: Decimal


class RunStatusResponse(BaseModel):
    id: int
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED"]
    summary: Optional[RunSummary] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ResultRow(BaseModel):
    id: int
    category: str
    confidence: Optional[Decimal]
    purchase: Optional[dict]
    gstr2b: Optional[dict]
    tax_delta: Optional[Decimal]
    date_delta_days: Optional[int]
    model_config = {"from_attributes": True}


class ResultsPageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ResultRow]
