from typing import Dict, List, Tuple
import pandas as pd
from rapidfuzz import process, fuzz

# Canonical field names for purchase register
PURCHASE_CANONICAL_FIELDS = [
    "invoice_number",
    "invoice_date",
    "supplier_gstin",
    "supplier_name",
    "taxable_amount",
    "igst",
    "cgst",
    "sgst",
    "total_tax",
    "invoice_type",
    "place_of_supply",
    "reverse_charge",
]

# Canonical field names for GSTR-2B
GSTR2B_CANONICAL_FIELDS = [
    "invoice_number",
    "invoice_date",
    "supplier_gstin",
    "supplier_name",
    "taxable_amount",
    "igst",
    "cgst",
    "sgst",
    "total_tax",
    "invoice_type",
    "place_of_supply",
    "itc_availability",
    "reason",
]

# Alias map: canonical_field -> list of known aliases
FIELD_ALIASES: Dict[str, List[str]] = {
    "invoice_number": [
        "invoice_number", "invoice no", "invoice_no", "inv no", "inv_no",
        "bill number", "bill_number", "doc_number", "document number",
        "voucher number", "voucher no", "invoice ref",
    ],
    "invoice_date": [
        "invoice_date", "invoice date", "inv date", "inv_date",
        "bill date", "document date", "voucher date", "date",
    ],
    "supplier_gstin": [
        "supplier_gstin", "supplier gstin", "gstin", "vendor gstin",
        "supplier gst", "party gstin", "gstin of supplier",
        "counter party gstin", "ctin",
    ],
    "supplier_name": [
        "supplier_name", "supplier name", "vendor name", "party name",
        "counter party name", "supplier", "vendor", "ledger name",
    ],
    "taxable_amount": [
        "taxable_amount", "taxable amount", "taxable value", "assessable value",
        "basic amount", "base amount", "net amount",
    ],
    "igst": [
        "igst", "igst amount", "integrated tax", "integrated gst",
        "igst_amount",
    ],
    "cgst": [
        "cgst", "cgst amount", "central tax", "central gst", "cgst_amount",
    ],
    "sgst": [
        "sgst", "sgst amount", "state tax", "state gst", "sgst_amount",
        "utgst", "utgst amount",
    ],
    "total_tax": [
        "total_tax", "total tax", "tax amount", "gst amount", "total gst",
        "total tax amount",
    ],
    "invoice_type": [
        "invoice_type", "invoice type", "supply type", "type",
        "transaction type",
    ],
    "place_of_supply": [
        "place_of_supply", "place of supply", "pos", "state code",
        "destination state",
    ],
    "reverse_charge": [
        "reverse_charge", "reverse charge", "rcm", "is_rcm",
    ],
    "itc_availability": [
        "itc_availability", "itc availability", "itc", "itc eligible",
        "eligible for itc",
    ],
    "reason": [
        "reason", "reason for ineligibility", "ineligibility reason",
        "remarks",
    ],
}


def auto_map(
    source_columns: List[str],
    canonical_fields: List[str],
    threshold: int = 75,
) -> Tuple[Dict[str, str], List[str]]:
    """
    Auto-detect mapping from canonical fields to source columns using fuzzy matching.

    Returns:
        detected: dict of {canonical_field: source_column}
        unresolved: list of canonical fields that couldn't be auto-mapped
    """
    detected: Dict[str, str] = {}
    used_source_cols = set()

    # Build a normalized lookup for source columns
    source_lower = {col: col.lower().strip() for col in source_columns}

    for canonical in canonical_fields:
        aliases = FIELD_ALIASES.get(canonical, [canonical])

        # First try exact match against aliases
        matched = None
        for col, col_lower in source_lower.items():
            if col_lower in aliases:
                matched = col
                break

        # If not exact, try fuzzy match
        if matched is None:
            all_aliases_str = " ".join(aliases)
            result = process.extractOne(
                all_aliases_str,
                source_columns,
                scorer=fuzz.token_set_ratio,
                score_cutoff=threshold,
            )
            if result:
                matched_col, score, _ = result
                if matched_col not in used_source_cols:
                    matched = matched_col

        # Also try matching canonical name directly
        if matched is None:
            result = process.extractOne(
                canonical,
                source_columns,
                scorer=fuzz.token_set_ratio,
                score_cutoff=threshold,
            )
            if result:
                matched_col, score, _ = result
                if matched_col not in used_source_cols:
                    matched = matched_col

        if matched and matched not in used_source_cols:
            detected[canonical] = matched
            used_source_cols.add(matched)

    unresolved = [f for f in canonical_fields if f not in detected]
    return detected, unresolved


def apply_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Apply column mapping to rename source columns to canonical names.
    Only keeps columns that are in the mapping.
    """
    # Reverse map: source_col -> canonical
    reverse = {v: k for k, v in mapping.items()}

    # Filter to only mapped columns
    available = {src: canon for src, canon in reverse.items() if src in df.columns}

    if not available:
        return df

    result = df[list(available.keys())].copy()
    result = result.rename(columns=available)
    return result
