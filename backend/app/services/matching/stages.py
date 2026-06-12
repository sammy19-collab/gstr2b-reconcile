"""
Multi-stage matching pipeline for GSTR-2B reconciliation.

Stage 0: Detect duplicates within each dataset
Stage 1: Exact match on (supplier_gstin_norm, invoice_number_norm)
Stage 2: Fuzzy match on invoice number within same GSTIN group
Stage 3: Residual classification (missing in 2B / missing in books)
"""
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process

from app.services.matching.scoring import confidence, invoice_similarity, vendor_similarity
from app.services.matching.categorizer import categorize_match


def stage_0_duplicates(df: pd.DataFrame, id_col: str = "id") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect duplicate invoices within a dataset.
    Duplicates are identified by same (supplier_gstin_norm, invoice_number_norm).
    Rows where ALL key columns are empty are never flagged as duplicates.

    Returns:
        clean_df: DataFrame with duplicates removed (keeping first)
        duplicates_df: DataFrame with duplicate rows
    """
    key_cols = ["supplier_gstin_norm", "invoice_number_norm"]
    available_keys = [c for c in key_cols if c in df.columns]

    if not available_keys:
        return df, pd.DataFrame()

    # Only deduplicate rows that have at least one non-empty key
    has_key = df[available_keys].apply(
        lambda row: any(str(v).strip() not in ("", "nan") for v in row), axis=1
    )
    df_keyed = df[has_key]
    df_no_key = df[~has_key]

    if df_keyed.empty:
        return df, pd.DataFrame()

    mask = df_keyed.duplicated(subset=available_keys, keep="first")
    clean_keyed = df_keyed[~mask]
    duplicates_df = df_keyed[mask].copy()

    clean_df = pd.concat([clean_keyed, df_no_key]).sort_index().copy()
    return clean_df, duplicates_df


def stage_1_exact(
    pr_df: pd.DataFrame,
    g2b_df: pd.DataFrame,
    tax_tolerance: float = 1.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Exact match on (supplier_gstin_norm, invoice_number_norm).

    Returns:
        matched_df: merged DataFrame of exact matches with delta columns
        pr_unmatched: purchase invoices with no match
        g2b_unmatched: GSTR-2B invoices with no match
    """
    merge_keys = []
    if "supplier_gstin_norm" in pr_df.columns and "supplier_gstin_norm" in g2b_df.columns:
        merge_keys.append("supplier_gstin_norm")
    if "invoice_number_norm" in pr_df.columns and "invoice_number_norm" in g2b_df.columns:
        merge_keys.append("invoice_number_norm")

    if not merge_keys:
        return pd.DataFrame(), pr_df, g2b_df

    pr_work = pr_df.copy().add_suffix("_pr")
    g2b_work = g2b_df.copy().add_suffix("_g2b")

    # Re-add merge keys without suffix for merging
    for key in merge_keys:
        pr_work[key] = pr_df[key].values
        g2b_work[key] = g2b_df[key].values

    matched = pd.merge(
        pr_work,
        g2b_work,
        on=merge_keys,
        how="inner",
        suffixes=("", ""),
    )

    if matched.empty:
        return pd.DataFrame(), pr_df, g2b_df

    # Compute tax delta
    pr_tax_col = "total_tax_pr" if "total_tax_pr" in matched.columns else None
    g2b_tax_col = "total_tax_g2b" if "total_tax_g2b" in matched.columns else None

    if pr_tax_col and g2b_tax_col:
        matched["tax_delta"] = (
            matched[g2b_tax_col].fillna(0) - matched[pr_tax_col].fillna(0)
        )
    else:
        matched["tax_delta"] = 0.0

    # Compute date delta
    pr_date = "invoice_date_pr" if "invoice_date_pr" in matched.columns else None
    g2b_date = "invoice_date_g2b" if "invoice_date_g2b" in matched.columns else None

    if pr_date and g2b_date:
        matched["date_delta_days"] = (
            pd.to_datetime(matched[g2b_date], errors="coerce") -
            pd.to_datetime(matched[pr_date], errors="coerce")
        ).dt.days
    else:
        matched["date_delta_days"] = None

    # Categorize
    matched["category"] = matched.apply(
        lambda row: _categorize_row(row, tax_tolerance, is_fuzzy=False), axis=1
    )

    # Confidence
    matched["confidence"] = matched.apply(
        lambda row: confidence(
            inv_score=100.0,
            gstin_match=True,
            tax_delta=float(row.get("tax_delta", 0)),
            tax_tolerance=tax_tolerance,
            vendor_score=vendor_similarity(
                str(row.get("supplier_name_norm_pr", "")),
                str(row.get("supplier_name_norm_g2b", "")),
            ),
        ),
        axis=1,
    )

    # Identify unmatched
    if "id_pr" in pr_work.columns:
        matched_pr_ids = set(matched["id_pr"].tolist())
        pr_unmatched = pr_df[~pr_df["id"].isin(matched_pr_ids)].copy() if "id" in pr_df.columns else pr_df.copy()
    else:
        pr_unmatched = pd.DataFrame(columns=pr_df.columns)

    if "id_g2b" in g2b_work.columns:
        matched_g2b_ids = set(matched["id_g2b"].tolist())
        g2b_unmatched = g2b_df[~g2b_df["id"].isin(matched_g2b_ids)].copy() if "id" in g2b_df.columns else g2b_df.copy()
    else:
        g2b_unmatched = pd.DataFrame(columns=g2b_df.columns)

    return matched, pr_unmatched, g2b_unmatched


def stage_2_fuzzy(
    pr_unmatched: pd.DataFrame,
    g2b_unmatched: pd.DataFrame,
    fuzzy_threshold: int = 80,
    tax_tolerance: float = 1.0,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fuzzy match on invoice number within same GSTIN group.

    Returns:
        fuzzy_matched: matched pairs with fuzzy match info
        pr_residual: still-unmatched purchase invoices
        g2b_residual: still-unmatched GSTR-2B invoices
    """
    if pr_unmatched.empty or g2b_unmatched.empty:
        return pd.DataFrame(), pr_unmatched, g2b_unmatched

    pr_work = pr_unmatched.copy()
    g2b_work = g2b_unmatched.copy()

    # Reset indexes
    pr_work = pr_work.reset_index(drop=True)
    g2b_work = g2b_work.reset_index(drop=True)

    fuzzy_pairs = []
    used_g2b_indices = set()

    gstin_col_pr = "supplier_gstin_norm" if "supplier_gstin_norm" in pr_work.columns else None
    gstin_col_g2b = "supplier_gstin_norm" if "supplier_gstin_norm" in g2b_work.columns else None
    inv_col_pr = "invoice_number_norm" if "invoice_number_norm" in pr_work.columns else None
    inv_col_g2b = "invoice_number_norm" if "invoice_number_norm" in g2b_work.columns else None

    # Need at least invoice number columns OR supplier name columns to attempt matching
    has_inv_cols = inv_col_pr and inv_col_g2b
    has_name_cols = (
        "supplier_name_norm" in pr_work.columns and
        "supplier_name_norm" in g2b_work.columns
    )
    if not has_inv_cols and not has_name_cols:
        return pd.DataFrame(), pr_unmatched, g2b_unmatched

    # Determine if GSTIN data is available in either dataset
    pr_has_gstin = (
        gstin_col_pr is not None and
        pr_work[gstin_col_pr].apply(lambda v: str(v).strip() not in ("", "nan")).any()
    )

    for pr_idx, pr_row in pr_work.iterrows():
        pr_gstin = str(pr_row[gstin_col_pr]).strip() if gstin_col_pr else ""
        pr_inv = str(pr_row[inv_col_pr]).strip() if inv_col_pr else ""

        if pr_has_gstin and pr_gstin and pr_inv:
            # Normal path: match by GSTIN group then fuzzy invoice number
            gstin_mask = g2b_work[gstin_col_g2b] == pr_gstin
            candidates = g2b_work[gstin_mask & ~g2b_work.index.isin(used_g2b_indices)]

            if candidates.empty:
                continue

            g2b_invoices = candidates[inv_col_g2b].tolist()
            result = process.extractOne(
                pr_inv,
                g2b_invoices,
                scorer=fuzz.token_set_ratio,
                score_cutoff=fuzzy_threshold,
            )

            if not result:
                continue

            matched_inv, score, match_pos = result
            g2b_idx = candidates.index[g2b_invoices.index(matched_inv)]
            g2b_row = g2b_work.loc[g2b_idx]
        else:
            # Fallback path (Tally / no-GSTIN exports): match by supplier name + invoice total
            pr_name = str(pr_row.get("supplier_name_norm", "")).strip()
            pr_total = float(pr_row.get("invoice_total", 0) or 0)

            if not pr_name and pr_total == 0:
                continue

            candidates = g2b_work[~g2b_work.index.isin(used_g2b_indices)]
            if candidates.empty:
                continue

            best_idx = None
            best_name_score = 0

            for g2b_idx_cand, g2b_row_cand in candidates.iterrows():
                g2b_name = str(g2b_row_cand.get("supplier_name_norm", "")).strip()
                g2b_total = float(g2b_row_cand.get("invoice_total", 0) or 0)

                name_score = fuzz.token_set_ratio(pr_name, g2b_name) if pr_name and g2b_name else 0
                if name_score < fuzzy_threshold:
                    continue

                # Invoice total must match within 1%
                if pr_total > 0 and g2b_total > 0:
                    if abs(pr_total - g2b_total) / max(pr_total, g2b_total) > 0.01:
                        continue
                elif pr_total != g2b_total:
                    continue

                if name_score > best_name_score:
                    best_name_score = name_score
                    best_idx = g2b_idx_cand

            if best_idx is None:
                continue

            g2b_row = g2b_work.loc[best_idx]
            g2b_idx = best_idx
            score = best_name_score

        tax_delta = _compute_tax_delta(pr_row, g2b_row)
        date_delta = _compute_date_delta(pr_row, g2b_row)

        category = categorize_match(
            is_matched=True,
            tax_delta=tax_delta,
            tax_tolerance=tax_tolerance,
            date_delta_days=date_delta,
            invoice_norm_pr=pr_inv,
            invoice_norm_g2b=str(g2b_row.get(inv_col_g2b, "")) if inv_col_g2b else "",
            gstin_match=(pr_gstin != "" and pr_gstin == str(g2b_row.get(gstin_col_g2b, "")).strip()),
            is_fuzzy=True,
        )

        conf = confidence(
            inv_score=float(score),
            gstin_match=(pr_gstin != "" and pr_gstin == str(g2b_row.get(gstin_col_g2b, "")).strip()),
            tax_delta=float(tax_delta) if tax_delta is not None else 0.0,
            tax_tolerance=tax_tolerance,
            vendor_score=vendor_similarity(
                str(pr_row.get("supplier_name_norm", "")),
                str(g2b_row.get("supplier_name_norm", "")),
            ),
        )

        fuzzy_pairs.append({
            "pr_idx": pr_idx,
            "g2b_idx": g2b_idx,
            "pr_row": pr_row,
            "g2b_row": g2b_row,
            "fuzzy_score": score,
            "tax_delta": tax_delta,
            "date_delta_days": date_delta,
            "category": category,
            "confidence": conf,
        })
        used_g2b_indices.add(g2b_idx)

    if not fuzzy_pairs:
        return pd.DataFrame(), pr_unmatched, g2b_unmatched

    used_pr_indices = {p["pr_idx"] for p in fuzzy_pairs}
    pr_residual = pr_work[~pr_work.index.isin(used_pr_indices)].copy()
    g2b_residual = g2b_work[~g2b_work.index.isin(used_g2b_indices)].copy()

    fuzzy_df = pd.DataFrame(fuzzy_pairs)
    return fuzzy_df, pr_residual, g2b_residual


def stage_3_residuals(
    pr_residual: pd.DataFrame,
    g2b_residual: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Classify remaining unmatched invoices.

    Returns:
        missing_in_2b_df: purchase invoices not in GSTR-2B
        missing_in_books_df: GSTR-2B invoices not in purchase register
    """
    missing_in_2b = pr_residual.copy()
    missing_in_2b["category"] = "MISSING_IN_2B"
    missing_in_2b["confidence"] = None
    missing_in_2b["tax_delta"] = None
    missing_in_2b["date_delta_days"] = None

    missing_in_books = g2b_residual.copy()
    missing_in_books["category"] = "MISSING_IN_BOOKS"
    missing_in_books["confidence"] = None
    missing_in_books["tax_delta"] = None
    missing_in_books["date_delta_days"] = None

    return missing_in_2b, missing_in_books


def _categorize_row(row: pd.Series, tax_tolerance: float, is_fuzzy: bool) -> str:
    tax_delta = row.get("tax_delta", 0) or 0
    date_delta = row.get("date_delta_days")
    inv_pr = str(row.get("invoice_number_norm_pr", row.get("invoice_number_norm", "")))
    inv_g2b = str(row.get("invoice_number_norm_g2b", row.get("invoice_number_norm", "")))

    return categorize_match(
        is_matched=True,
        tax_delta=float(tax_delta),
        tax_tolerance=tax_tolerance,
        date_delta_days=int(date_delta) if date_delta is not None and not pd.isna(date_delta) else None,
        invoice_norm_pr=inv_pr,
        invoice_norm_g2b=inv_g2b,
        gstin_match=True,
        is_fuzzy=is_fuzzy,
    )


def _compute_tax_delta(pr_row: pd.Series, g2b_row: pd.Series) -> float:
    pr_tax = float(pr_row.get("total_tax", 0) or 0)
    g2b_tax = float(g2b_row.get("total_tax", 0) or 0)
    return g2b_tax - pr_tax


def _compute_date_delta(pr_row: pd.Series, g2b_row: pd.Series) -> int:
    pr_date = pd.to_datetime(pr_row.get("invoice_date"), errors="coerce")
    g2b_date = pd.to_datetime(g2b_row.get("invoice_date"), errors="coerce")
    if pd.isna(pr_date) or pd.isna(g2b_date):
        return None
    return (g2b_date - pr_date).days
