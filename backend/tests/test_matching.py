"""
Unit tests for the matching engine stages.
Tests: exact match, tax mismatch, fuzzy match, missing_in_2b, missing_in_books, duplicate detection.
"""
import pytest
import pandas as pd
from decimal import Decimal

from app.services.matching.stages import (
    stage_0_duplicates,
    stage_1_exact,
    stage_2_fuzzy,
    stage_3_residuals,
)
from app.services.matching.scoring import confidence, invoice_similarity
from app.services.cleaning import clean_purchase_df, clean_gstr2b_df, norm_invoice, norm_gstin


def make_pr_df(rows):
    """Helper to create a purchase register DataFrame."""
    df = pd.DataFrame(rows)
    return clean_purchase_df(df)


def make_g2b_df(rows):
    """Helper to create a GSTR-2B DataFrame."""
    df = pd.DataFrame(rows)
    return clean_gstr2b_df(df)


# ============================================================
# Test: norm_invoice
# ============================================================

def test_norm_invoice_basic():
    assert norm_invoice("INV-001") == "INV001"
    assert norm_invoice("inv 001") == "INV001"
    assert norm_invoice("  INV/001  ") == "INV001"
    assert norm_invoice(None) == ""


def test_norm_gstin_basic():
    assert norm_gstin("27AAPFU0939F1ZV") == "27AAPFU0939F1ZV"
    assert norm_gstin("  27aapfu0939f1zv  ") == "27AAPFU0939F1ZV"
    assert norm_gstin(None) == ""


# ============================================================
# Test: stage_0_duplicates
# ============================================================

def test_stage_0_no_duplicates():
    pr = make_pr_df([
        {"invoice_number": "INV-001", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "100"},
        {"invoice_number": "INV-002", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "200"},
    ])
    pr["id"] = range(len(pr))
    clean, dups = stage_0_duplicates(pr)
    assert len(clean) == 2
    assert len(dups) == 0


def test_stage_0_with_duplicates():
    pr = make_pr_df([
        {"invoice_number": "INV-001", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "100"},
        {"invoice_number": "INV-001", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "100"},
        {"invoice_number": "INV-002", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "200"},
    ])
    pr["id"] = range(len(pr))
    clean, dups = stage_0_duplicates(pr)
    assert len(clean) == 2
    assert len(dups) == 1


# ============================================================
# Test: stage_1_exact — exact match
# ============================================================

def test_stage_1_exact_match():
    pr = make_pr_df([
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Acme Corp", "total_tax": "1000", "invoice_date": "01/01/2024"},
    ])
    pr["id"] = range(len(pr))

    g2b = make_g2b_df([
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Acme Corp", "total_tax": "1000", "invoice_date": "01/01/2024"},
    ])
    g2b["id"] = range(len(g2b))

    matched, pr_unmatched, g2b_unmatched = stage_1_exact(pr, g2b, tax_tolerance=1.0)

    assert len(matched) == 1
    assert len(pr_unmatched) == 0
    assert len(g2b_unmatched) == 0
    assert matched.iloc[0]["category"] == "EXACT_MATCH"


def test_stage_1_tax_mismatch():
    pr = make_pr_df([
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Acme Corp", "total_tax": "1000", "invoice_date": "01/01/2024"},
    ])
    pr["id"] = range(len(pr))

    g2b = make_g2b_df([
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Acme Corp", "total_tax": "1100", "invoice_date": "01/01/2024"},
    ])
    g2b["id"] = range(len(g2b))

    matched, pr_unmatched, g2b_unmatched = stage_1_exact(pr, g2b, tax_tolerance=1.0)

    assert len(matched) == 1
    assert matched.iloc[0]["category"] == "TAX_MISMATCH"
    assert abs(float(matched.iloc[0]["tax_delta"])) == 100.0


def test_stage_1_no_match():
    pr = make_pr_df([
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "1000"},
    ])
    pr["id"] = range(len(pr))

    g2b = make_g2b_df([
        {"invoice_number": "INV999", "supplier_gstin": "29AAPFU0939F1ZV", "total_tax": "1000"},
    ])
    g2b["id"] = range(len(g2b))

    matched, pr_unmatched, g2b_unmatched = stage_1_exact(pr, g2b, tax_tolerance=1.0)

    assert len(matched) == 0
    assert len(pr_unmatched) == 1
    assert len(g2b_unmatched) == 1


# ============================================================
# Test: stage_2_fuzzy — fuzzy match
# ============================================================

def test_stage_2_fuzzy_match():
    pr = make_pr_df([
        {"invoice_number": "ACME/2024/001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Acme Corp", "total_tax": "1000"},
    ])
    pr["id"] = range(len(pr))

    g2b = make_g2b_df([
        {"invoice_number": "ACME-2024-001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Acme Corp", "total_tax": "1000"},
    ])
    g2b["id"] = range(len(g2b))

    fuzzy_matched, pr_residual, g2b_residual = stage_2_fuzzy(
        pr, g2b, fuzzy_threshold=70, tax_tolerance=1.0
    )

    assert not fuzzy_matched.empty
    assert len(fuzzy_matched) == 1
    assert len(pr_residual) == 0
    assert len(g2b_residual) == 0


# ============================================================
# Test: stage_3_residuals — missing in 2B and missing in books
# ============================================================

def test_stage_3_missing_in_2b():
    pr_residual = make_pr_df([
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "500"},
        {"invoice_number": "INV002", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "300"},
    ])
    g2b_residual = make_g2b_df([])

    missing_in_2b, missing_in_books = stage_3_residuals(pr_residual, g2b_residual)

    assert len(missing_in_2b) == 2
    assert all(missing_in_2b["category"] == "MISSING_IN_2B")
    assert len(missing_in_books) == 0


def test_stage_3_missing_in_books():
    pr_residual = make_pr_df([])
    g2b_residual = make_g2b_df([
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV", "total_tax": "500"},
    ])

    missing_in_2b, missing_in_books = stage_3_residuals(pr_residual, g2b_residual)

    assert len(missing_in_2b) == 0
    assert len(missing_in_books) == 1
    assert all(missing_in_books["category"] == "MISSING_IN_BOOKS")


# ============================================================
# Test: confidence scoring
# ============================================================

def test_confidence_perfect_match():
    score = confidence(
        inv_score=100.0,
        gstin_match=True,
        tax_delta=0.0,
        tax_tolerance=1.0,
        vendor_score=100.0,
    )
    assert score == Decimal("100.00")


def test_confidence_partial_match():
    score = confidence(
        inv_score=80.0,
        gstin_match=True,
        tax_delta=5.0,
        tax_tolerance=1.0,
        vendor_score=70.0,
    )
    # 30 (gstin) + 32 (inv 80/100*40) + 0 (tax out of tolerance) + 7 (vendor 70/100*10) = 69
    assert float(score) == pytest.approx(69.0, abs=0.5)


def test_invoice_similarity():
    score = invoice_similarity("ACME2024001", "ACME2024001")
    assert score == 100.0

    score = invoice_similarity("ACME2024001", "ACME2024002")
    assert score > 80.0

    score = invoice_similarity("INV001", "XYZ999")
    assert score < 50.0


# ============================================================
# Test: full pipeline integration
# ============================================================

def test_full_pipeline_mixed():
    """Test a mixed dataset with exact, tax mismatch, and missing invoices."""
    pr = make_pr_df([
        # Exact match
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Vendor A", "total_tax": "1000"},
        # Tax mismatch (will match by key but tax differs)
        {"invoice_number": "INV002", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Vendor A", "total_tax": "500"},
        # Missing in 2B
        {"invoice_number": "INV003", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Vendor A", "total_tax": "200"},
    ])
    pr["id"] = range(len(pr))

    g2b = make_g2b_df([
        # Exact match for INV001
        {"invoice_number": "INV001", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Vendor A", "total_tax": "1000"},
        # Tax mismatch for INV002
        {"invoice_number": "INV002", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Vendor A", "total_tax": "600"},
        # Missing in books (only in 2B)
        {"invoice_number": "INV004", "supplier_gstin": "27AAPFU0939F1ZV",
         "supplier_name": "Vendor A", "total_tax": "300"},
    ])
    g2b["id"] = range(len(g2b))

    # Stage 0
    pr_clean, pr_dups = stage_0_duplicates(pr)
    g2b_clean, g2b_dups = stage_0_duplicates(g2b)
    assert len(pr_dups) == 0
    assert len(g2b_dups) == 0

    # Stage 1
    matched, pr_unmatched, g2b_unmatched = stage_1_exact(pr_clean, g2b_clean, tax_tolerance=1.0)
    assert len(matched) == 2  # INV001 exact, INV002 tax mismatch

    categories = matched["category"].tolist()
    assert "EXACT_MATCH" in categories
    assert "TAX_MISMATCH" in categories

    # Stage 3
    missing_in_2b, missing_in_books = stage_3_residuals(pr_unmatched, g2b_unmatched)
    assert len(missing_in_2b) == 1  # INV003
    assert len(missing_in_books) == 1  # INV004
