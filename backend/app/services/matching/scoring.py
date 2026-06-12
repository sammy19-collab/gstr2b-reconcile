from decimal import Decimal
from typing import Optional
import pandas as pd
from rapidfuzz import fuzz


def confidence(
    inv_score: float = 0.0,
    gstin_match: bool = False,
    tax_delta: float = 0.0,
    tax_tolerance: float = 1.0,
    vendor_score: float = 0.0,
) -> Decimal:
    """
    Compute a composite confidence score (0-100) for a match.

    Weights:
    - GSTIN match: 30 pts
    - Invoice number similarity: 40 pts
    - Tax within tolerance: 20 pts
    - Vendor name similarity: 10 pts
    """
    score = 0.0

    # GSTIN match
    if gstin_match:
        score += 30.0

    # Invoice number similarity (0-100 scaled to 40)
    score += (inv_score / 100.0) * 40.0

    # Tax delta within tolerance
    if abs(tax_delta) <= tax_tolerance:
        score += 20.0

    # Vendor name similarity (0-100 scaled to 10)
    score += (vendor_score / 100.0) * 10.0

    return Decimal(str(round(min(score, 100.0), 2)))


def invoice_similarity(inv1: str, inv2: str) -> float:
    """Compute similarity score between two invoice numbers."""
    if not inv1 or not inv2:
        return 0.0
    return fuzz.token_set_ratio(inv1, inv2)


def vendor_similarity(name1: str, name2: str) -> float:
    """Compute similarity score between two vendor names."""
    if not name1 or not name2:
        return 0.0
    return fuzz.token_set_ratio(name1, name2)
