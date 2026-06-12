from typing import Optional
from decimal import Decimal


def categorize_match(
    is_matched: bool,
    tax_delta: Optional[float],
    tax_tolerance: float,
    date_delta_days: Optional[int],
    invoice_norm_pr: str,
    invoice_norm_g2b: str,
    gstin_match: bool,
    is_fuzzy: bool = False,
) -> str:
    """
    Categorize a matched pair into a MatchCategory string.

    Priority order:
    1. If not matched at all -> will be handled by missing stages
    2. Exact match (all fields match within tolerance)
    3. Tax mismatch (invoices match but tax differs)
    4. Invoice mismatch (GSTIN/vendor matches but invoice number differs)
    5. Date mismatch (invoice/tax match but date differs > 5 days)
    6. Fuzzy match (fuzzy invoice match)
    """
    if not is_matched:
        return "MISSING_IN_2B"

    tax_ok = tax_delta is None or abs(tax_delta) <= tax_tolerance

    if invoice_norm_pr == invoice_norm_g2b and gstin_match and tax_ok:
        if date_delta_days is not None and abs(date_delta_days) > 5:
            return "DATE_MISMATCH"
        return "EXACT_MATCH"

    if invoice_norm_pr == invoice_norm_g2b and gstin_match and not tax_ok:
        return "TAX_MISMATCH"

    if gstin_match and not tax_ok:
        return "TAX_MISMATCH"

    if gstin_match and invoice_norm_pr != invoice_norm_g2b:
        return "INVOICE_MISMATCH"

    if is_fuzzy:
        return "FUZZY_MATCH"

    if date_delta_days is not None and abs(date_delta_days) > 5:
        return "DATE_MISMATCH"

    return "FUZZY_MATCH"
