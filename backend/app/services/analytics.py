from typing import List, Dict, Any
from decimal import Decimal
import pandas as pd


def build_summary(results: List) -> Dict[str, Any]:
    """
    Build a run summary from a list of ReconciliationResult objects.
    """
    counts = {
        "total_invoices": len(results),
        "total_matched": 0,
        "missing_in_2b": 0,
        "missing_in_books": 0,
        "tax_mismatch": 0,
        "invoice_mismatch": 0,
        "date_mismatch": 0,
        "duplicates": 0,
    }
    itc_available = Decimal("0")
    itc_at_risk = Decimal("0")

    for result in results:
        cat = result.category.value if result.category else ""

        if cat == "EXACT_MATCH":
            counts["total_matched"] += 1
            if result.gstr2b_data:
                tax = result.gstr2b_data.get("total_tax") or 0
                itc_available += Decimal(str(tax))
        elif cat == "FUZZY_MATCH":
            counts["total_matched"] += 1
            if result.gstr2b_data:
                tax = result.gstr2b_data.get("total_tax") or 0
                itc_available += Decimal(str(tax))
        elif cat == "TAX_MISMATCH":
            counts["tax_mismatch"] += 1
            if result.tax_delta:
                itc_at_risk += abs(result.tax_delta)
        elif cat == "INVOICE_MISMATCH":
            counts["invoice_mismatch"] += 1
            itc_at_risk += Decimal("0")
        elif cat == "DATE_MISMATCH":
            counts["date_mismatch"] += 1
            counts["total_matched"] += 1
        elif cat == "MISSING_IN_2B":
            counts["missing_in_2b"] += 1
            if result.purchase_data:
                tax = result.purchase_data.get("total_tax") or 0
                itc_at_risk += Decimal(str(tax))
        elif cat == "MISSING_IN_BOOKS":
            counts["missing_in_books"] += 1
        elif cat == "DUPLICATE":
            counts["duplicates"] += 1

    return {
        **counts,
        "itc_available": str(itc_available),
        "itc_at_risk": str(itc_at_risk),
    }


def aggregate_vendor_analytics(results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate reconciliation results DataFrame by vendor for analytics.
    """
    if results_df.empty:
        return pd.DataFrame()

    records = []
    for gstin, group in results_df.groupby("supplier_gstin", dropna=False):
        total = len(group)
        matched = len(group[group["category"].isin(["EXACT_MATCH", "FUZZY_MATCH", "DATE_MISMATCH"])])
        missing_2b = len(group[group["category"] == "MISSING_IN_2B"])
        missing_books = len(group[group["category"] == "MISSING_IN_BOOKS"])
        tax_mismatch = len(group[group["category"] == "TAX_MISMATCH"])

        records.append({
            "supplier_gstin": gstin,
            "total_invoices": total,
            "matched": matched,
            "missing_in_2b": missing_2b,
            "missing_in_books": missing_books,
            "tax_mismatch": tax_mismatch,
        })

    return pd.DataFrame(records)
