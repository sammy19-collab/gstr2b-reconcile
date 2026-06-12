"""
Main reconciliation engine orchestrator.
Loads invoices from DB, runs matching stages, and writes results.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.invoice import PurchaseInvoice, Gstr2bInvoice
from app.models.reconciliation import ReconciliationRun, ReconciliationResult, MatchCategory, RunStatus
from app.models.vendor import VendorAnalytics
from app.models.upload import Upload, ColumnMapping
from app.services.ingestion import parse_file_to_dataframe
from app.services.mapping import apply_mapping
from app.services.cleaning import clean_purchase_df, clean_gstr2b_df
from app.services.matching.stages import (
    stage_0_duplicates,
    stage_1_exact,
    stage_2_fuzzy,
    stage_3_residuals,
)
from app.services.analytics import aggregate_vendor_analytics, build_summary


def run_reconciliation_engine(run_id: int, db: Session) -> None:
    """
    Main entry point. Loads data, runs all matching stages, persists results.
    """
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    run.status = RunStatus.RUNNING
    db.commit()

    try:
        # Load and prepare DataFrames
        pr_df = _load_upload_df(run.pr_upload_id, db, "purchase")
        g2b_df = _load_upload_df(run.g2b_upload_id, db, "gstr2b")

        tax_tolerance = float(run.tax_tolerance)
        fuzzy_threshold = run.fuzzy_threshold

        # Stage 0: detect duplicates
        pr_clean, pr_dups = stage_0_duplicates(pr_df)
        g2b_clean, g2b_dups = stage_0_duplicates(g2b_df)

        # Stage 1: exact match
        exact_matched, pr_unmatched, g2b_unmatched = stage_1_exact(
            pr_clean, g2b_clean, tax_tolerance=tax_tolerance
        )

        # Stage 2: fuzzy match
        fuzzy_matched, pr_residual, g2b_residual = stage_2_fuzzy(
            pr_unmatched, g2b_unmatched,
            fuzzy_threshold=fuzzy_threshold,
            tax_tolerance=tax_tolerance,
        )

        # Stage 3: residuals
        missing_in_2b, missing_in_books = stage_3_residuals(pr_residual, g2b_residual)

        # Persist results
        results: List[ReconciliationResult] = []

        # Exact matches
        for _, row in exact_matched.iterrows():
            result = _make_result_from_matched_row(run_id, row, is_fuzzy=False)
            results.append(result)

        # Fuzzy matches
        for _, row in fuzzy_matched.iterrows() if not fuzzy_matched.empty else []:
            result = _make_result_from_fuzzy_row(run_id, row)
            results.append(result)

        # Duplicates
        for _, row in pr_dups.iterrows():
            result = ReconciliationResult(
                run_id=run_id,
                category=MatchCategory.DUPLICATE,
                confidence=Decimal("50.00"),
                purchase_data=_row_to_dict(row),
                gstr2b_data=None,
                tax_delta=None,
                date_delta_days=None,
            )
            results.append(result)

        for _, row in g2b_dups.iterrows():
            result = ReconciliationResult(
                run_id=run_id,
                category=MatchCategory.DUPLICATE,
                confidence=Decimal("50.00"),
                purchase_data=None,
                gstr2b_data=_row_to_dict(row),
                tax_delta=None,
                date_delta_days=None,
            )
            results.append(result)

        # Missing in 2B
        for _, row in missing_in_2b.iterrows():
            result = ReconciliationResult(
                run_id=run_id,
                category=MatchCategory.MISSING_IN_2B,
                confidence=None,
                purchase_data=_row_to_dict(row),
                gstr2b_data=None,
                tax_delta=None,
                date_delta_days=None,
            )
            results.append(result)

        # Missing in books
        for _, row in missing_in_books.iterrows():
            result = ReconciliationResult(
                run_id=run_id,
                category=MatchCategory.MISSING_IN_BOOKS,
                confidence=None,
                purchase_data=None,
                gstr2b_data=_row_to_dict(row),
                tax_delta=None,
                date_delta_days=None,
            )
            results.append(result)

        # Bulk insert results
        db.bulk_save_objects(results)
        db.flush()

        # Compute analytics
        results_list = db.query(ReconciliationResult).filter(
            ReconciliationResult.run_id == run_id
        ).all()

        vendor_analytics = _compute_vendor_analytics(run_id, results_list)
        db.bulk_save_objects(vendor_analytics)
        db.flush()

        # Build summary
        summary = build_summary(results_list)

        run.status = RunStatus.COMPLETED
        run.summary = summary
        run.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
        if run:
            run.status = RunStatus.FAILED
            run.error_message = str(e)[:1024]
            db.commit()
        raise


def _load_upload_df(upload_id: int, db: Session, upload_kind: str) -> pd.DataFrame:
    """Load an upload file into a DataFrame with column mapping applied."""
    from app.config import get_settings
    settings = get_settings()

    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise ValueError(f"Upload {upload_id} not found")

    df = parse_file_to_dataframe(upload.filepath, settings.MAX_ROWS)

    # Apply column mapping if exists
    col_mapping = db.query(ColumnMapping).filter(ColumnMapping.upload_id == upload_id).first()
    if col_mapping and col_mapping.mapping:
        df = apply_mapping(df, col_mapping.mapping)

    # Clean the DataFrame
    if upload_kind == "purchase":
        df = clean_purchase_df(df)
    else:
        df = clean_gstr2b_df(df)

    # Add a local index as 'id' for matching
    df["id"] = range(len(df))
    return df


def _make_result_from_matched_row(run_id: int, row: pd.Series, is_fuzzy: bool) -> ReconciliationResult:
    """Create a ReconciliationResult from an exact-matched row."""
    category_str = str(row.get("category", "EXACT_MATCH"))
    try:
        category = MatchCategory(category_str)
    except ValueError:
        category = MatchCategory.EXACT_MATCH

    tax_delta = row.get("tax_delta")
    date_delta = row.get("date_delta_days")
    conf = row.get("confidence")

    pr_data = _extract_side_data(row, suffix="_pr")
    g2b_data = _extract_side_data(row, suffix="_g2b")

    return ReconciliationResult(
        run_id=run_id,
        category=category,
        confidence=Decimal(str(round(float(conf), 2))) if conf is not None else None,
        purchase_data=pr_data,
        gstr2b_data=g2b_data,
        tax_delta=Decimal(str(round(float(tax_delta), 2))) if tax_delta is not None else None,
        date_delta_days=int(date_delta) if date_delta is not None and not pd.isna(date_delta) else None,
    )


def _make_result_from_fuzzy_row(run_id: int, row: pd.Series) -> ReconciliationResult:
    """Create a ReconciliationResult from a fuzzy-matched row."""
    category_str = str(row.get("category", "FUZZY_MATCH"))
    try:
        category = MatchCategory(category_str)
    except ValueError:
        category = MatchCategory.FUZZY_MATCH

    conf = row.get("confidence")
    tax_delta = row.get("tax_delta")
    date_delta = row.get("date_delta_days")

    pr_row = row.get("pr_row")
    g2b_row = row.get("g2b_row")

    pr_data = _row_to_dict(pr_row) if pr_row is not None else None
    g2b_data = _row_to_dict(g2b_row) if g2b_row is not None else None

    return ReconciliationResult(
        run_id=run_id,
        category=category,
        confidence=Decimal(str(round(float(conf), 2))) if conf is not None else None,
        purchase_data=pr_data,
        gstr2b_data=g2b_data,
        tax_delta=Decimal(str(round(float(tax_delta), 2))) if tax_delta is not None else None,
        date_delta_days=int(date_delta) if date_delta is not None and not pd.isna(date_delta) else None,
    )


def _extract_side_data(row: pd.Series, suffix: str) -> Dict[str, Any]:
    """Extract one side (pr or g2b) of a merged row."""
    data = {}
    for col in row.index:
        if col.endswith(suffix):
            key = col[:-len(suffix)]
            val = row[col]
            if isinstance(val, float) and np.isnan(val):
                data[key] = None
            elif isinstance(val, pd.Timestamp):
                data[key] = val.isoformat() if not pd.isna(val) else None
            else:
                data[key] = val
    return data


def _row_to_dict(row: pd.Series) -> Dict[str, Any]:
    """Convert a Series row to a JSON-serializable dict."""
    if row is None:
        return {}
    result = {}
    for col, val in row.items():
        if val is None:
            result[col] = None
        elif isinstance(val, float) and np.isnan(val):
            result[col] = None
        elif isinstance(val, pd.Timestamp):
            result[col] = val.isoformat() if not pd.isna(val) else None
        elif hasattr(val, 'isoformat'):  # datetime, date objects
            result[col] = val.isoformat()
        elif isinstance(val, (np.integer,)):
            result[col] = int(val)
        elif isinstance(val, (np.floating,)):
            result[col] = float(val) if not np.isnan(val) else None
        elif isinstance(val, np.bool_):
            result[col] = bool(val)
        else:
            result[col] = val
    return result


def _compute_vendor_analytics(
    run_id: int,
    results: List[ReconciliationResult],
) -> List[VendorAnalytics]:
    """Aggregate results by vendor GSTIN."""
    vendor_map: Dict[str, Dict] = {}

    for result in results:
        gstin = None
        name = None

        if result.purchase_data:
            gstin = result.purchase_data.get("supplier_gstin") or result.purchase_data.get("supplier_gstin_norm")
            name = result.purchase_data.get("supplier_name") or result.purchase_data.get("supplier_name_norm")
        elif result.gstr2b_data:
            gstin = result.gstr2b_data.get("supplier_gstin") or result.gstr2b_data.get("supplier_gstin_norm")
            name = result.gstr2b_data.get("supplier_name") or result.gstr2b_data.get("supplier_name_norm")

        key = gstin or "UNKNOWN"
        if key not in vendor_map:
            vendor_map[key] = {
                "supplier_gstin": gstin,
                "supplier_name": name,
                "total_invoices": 0,
                "matched": 0,
                "missing_in_2b": 0,
                "missing_in_books": 0,
                "tax_mismatch": 0,
                "itc_available": Decimal("0"),
                "itc_at_risk": Decimal("0"),
            }

        vendor_map[key]["total_invoices"] += 1
        cat = result.category.value if result.category else ""

        if cat in ("EXACT_MATCH", "FUZZY_MATCH", "DATE_MISMATCH"):
            vendor_map[key]["matched"] += 1
            # ITC from g2b
            if result.gstr2b_data:
                tax = result.gstr2b_data.get("total_tax") or 0
                vendor_map[key]["itc_available"] += Decimal(str(tax))
        elif cat == "TAX_MISMATCH":
            vendor_map[key]["tax_mismatch"] += 1
            if result.tax_delta:
                vendor_map[key]["itc_at_risk"] += abs(result.tax_delta)
        elif cat == "MISSING_IN_2B":
            vendor_map[key]["missing_in_2b"] += 1
            if result.purchase_data:
                tax = result.purchase_data.get("total_tax") or 0
                vendor_map[key]["itc_at_risk"] += Decimal(str(tax))
        elif cat == "MISSING_IN_BOOKS":
            vendor_map[key]["missing_in_books"] += 1
            if result.gstr2b_data:
                tax = result.gstr2b_data.get("total_tax") or 0
                vendor_map[key]["itc_available"] += Decimal(str(tax))
        elif cat == "INVOICE_MISMATCH":
            vendor_map[key]["itc_at_risk"] += Decimal("0")

    analytics = []
    for key, data in vendor_map.items():
        va = VendorAnalytics(
            run_id=run_id,
            supplier_gstin=data["supplier_gstin"],
            supplier_name=data["supplier_name"],
            total_invoices=data["total_invoices"],
            matched=data["matched"],
            missing_in_2b=data["missing_in_2b"],
            missing_in_books=data["missing_in_books"],
            tax_mismatch=data["tax_mismatch"],
            itc_available=data["itc_available"],
            itc_at_risk=data["itc_at_risk"],
        )
        analytics.append(va)

    return analytics
