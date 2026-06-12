"""
Generate multi-sheet Excel report for a reconciliation run.
"""
import io
from decimal import Decimal
from typing import List, Optional
import xlsxwriter
from sqlalchemy.orm import Session

from app.models.reconciliation import ReconciliationRun, ReconciliationResult, MatchCategory
from app.models.vendor import VendorAnalytics


def generate_excel_report(run_id: int, db: Session) -> bytes:
    """Generate a multi-sheet Excel workbook for the given run."""
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    results = db.query(ReconciliationResult).filter(ReconciliationResult.run_id == run_id).all()
    vendors = db.query(VendorAnalytics).filter(VendorAnalytics.run_id == run_id).all()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # Formats
    header_fmt = workbook.add_format({
        "bold": True, "bg_color": "#1F4E79", "font_color": "#FFFFFF",
        "border": 1, "align": "center",
    })
    money_fmt = workbook.add_format({"num_format": "#,##0.00", "border": 1})
    date_fmt = workbook.add_format({"num_format": "dd/mm/yyyy", "border": 1})
    cell_fmt = workbook.add_format({"border": 1})
    green_fmt = workbook.add_format({"bg_color": "#C6EFCE", "border": 1})
    red_fmt = workbook.add_format({"bg_color": "#FFC7CE", "border": 1})
    yellow_fmt = workbook.add_format({"bg_color": "#FFEB9C", "border": 1})

    # 1. Summary sheet
    _write_summary_sheet(workbook, run, results, header_fmt, cell_fmt, money_fmt)

    # 2. Exact Match
    exact = [r for r in results if r.category == MatchCategory.EXACT_MATCH]
    _write_results_sheet(workbook, "Exact Match", exact, header_fmt, cell_fmt, money_fmt, green_fmt)

    # 3. Missing in 2B
    miss2b = [r for r in results if r.category == MatchCategory.MISSING_IN_2B]
    _write_results_sheet(workbook, "Missing in 2B", miss2b, header_fmt, cell_fmt, money_fmt, red_fmt)

    # 4. Missing in Books
    miss_books = [r for r in results if r.category == MatchCategory.MISSING_IN_BOOKS]
    _write_results_sheet(workbook, "Missing in Books", miss_books, header_fmt, cell_fmt, money_fmt, red_fmt)

    # 5. Tax Mismatch
    tax_mis = [r for r in results if r.category == MatchCategory.TAX_MISMATCH]
    _write_results_sheet(workbook, "Tax Mismatch", tax_mis, header_fmt, cell_fmt, money_fmt, yellow_fmt)

    # 6. Invoice Mismatch
    inv_mis = [r for r in results if r.category == MatchCategory.INVOICE_MISMATCH]
    _write_results_sheet(workbook, "Invoice Mismatch", inv_mis, header_fmt, cell_fmt, money_fmt, yellow_fmt)

    # 7. Vendor Summary
    _write_vendor_sheet(workbook, vendors, header_fmt, cell_fmt, money_fmt)

    workbook.close()
    output.seek(0)
    return output.read()


def _write_summary_sheet(workbook, run, results, header_fmt, cell_fmt, money_fmt):
    ws = workbook.add_worksheet("Summary")
    ws.set_column(0, 0, 30)
    ws.set_column(1, 1, 20)

    ws.write(0, 0, "GST Reconcile AI - Run Summary", header_fmt)
    ws.merge_range(0, 0, 0, 1, "GST Reconcile AI - Run Summary", header_fmt)

    rows = [
        ("Run ID", run.id),
        ("Period", run.period),
        ("Status", run.status.value),
        ("Created At", str(run.created_at)[:19] if run.created_at else ""),
        ("Completed At", str(run.completed_at)[:19] if run.completed_at else ""),
        ("", ""),
    ]

    if run.summary:
        s = run.summary
        rows += [
            ("Total Invoices", s.get("total_invoices", 0)),
            ("Total Matched", s.get("total_matched", 0)),
            ("Missing in 2B", s.get("missing_in_2b", 0)),
            ("Missing in Books", s.get("missing_in_books", 0)),
            ("Tax Mismatch", s.get("tax_mismatch", 0)),
            ("Invoice Mismatch", s.get("invoice_mismatch", 0)),
            ("Date Mismatch", s.get("date_mismatch", 0)),
            ("Duplicates", s.get("duplicates", 0)),
            ("ITC Available (₹)", float(s.get("itc_available", 0))),
            ("ITC At Risk (₹)", float(s.get("itc_at_risk", 0))),
        ]

    for i, (label, value) in enumerate(rows, start=2):
        ws.write(i, 0, label, cell_fmt)
        if isinstance(value, float):
            ws.write(i, 1, value, money_fmt)
        else:
            ws.write(i, 1, value, cell_fmt)


def _write_results_sheet(workbook, sheet_name, results, header_fmt, cell_fmt, money_fmt, row_fmt):
    ws = workbook.add_worksheet(sheet_name[:31])

    headers = [
        "Category", "Confidence",
        "PR Invoice No", "PR Date", "PR GSTIN", "PR Supplier", "PR Tax",
        "2B Invoice No", "2B Date", "2B GSTIN", "2B Supplier", "2B Tax",
        "Tax Delta", "Date Delta (Days)",
    ]

    col_widths = [15, 10, 20, 12, 18, 25, 12, 20, 12, 18, 25, 12, 10, 10]
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        ws.set_column(i, i, w)
        ws.write(0, i, h, header_fmt)

    for row_num, result in enumerate(results, start=1):
        pr = result.purchase_data or {}
        g2b = result.gstr2b_data or {}

        ws.write(row_num, 0, result.category.value, row_fmt)
        ws.write(row_num, 1, float(result.confidence) if result.confidence else "", cell_fmt)
        ws.write(row_num, 2, pr.get("invoice_number", ""), cell_fmt)
        ws.write(row_num, 3, pr.get("invoice_date", ""), cell_fmt)
        ws.write(row_num, 4, pr.get("supplier_gstin", ""), cell_fmt)
        ws.write(row_num, 5, pr.get("supplier_name", ""), cell_fmt)
        ws.write(row_num, 6, float(pr.get("total_tax") or 0), money_fmt)
        ws.write(row_num, 7, g2b.get("invoice_number", ""), cell_fmt)
        ws.write(row_num, 8, g2b.get("invoice_date", ""), cell_fmt)
        ws.write(row_num, 9, g2b.get("supplier_gstin", ""), cell_fmt)
        ws.write(row_num, 10, g2b.get("supplier_name", ""), cell_fmt)
        ws.write(row_num, 11, float(g2b.get("total_tax") or 0), money_fmt)
        ws.write(row_num, 12, float(result.tax_delta) if result.tax_delta else 0, money_fmt)
        ws.write(row_num, 13, result.date_delta_days if result.date_delta_days is not None else "", cell_fmt)


def _write_vendor_sheet(workbook, vendors, header_fmt, cell_fmt, money_fmt):
    ws = workbook.add_worksheet("Vendor Summary")

    headers = [
        "Supplier GSTIN", "Supplier Name",
        "Total Invoices", "Matched",
        "Missing in 2B", "Missing in Books", "Tax Mismatch",
        "ITC Available (₹)", "ITC At Risk (₹)",
    ]

    col_widths = [18, 30, 14, 10, 14, 16, 12, 18, 15]
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        ws.set_column(i, i, w)
        ws.write(0, i, h, header_fmt)

    for row_num, vendor in enumerate(vendors, start=1):
        ws.write(row_num, 0, vendor.supplier_gstin or "", cell_fmt)
        ws.write(row_num, 1, vendor.supplier_name or "", cell_fmt)
        ws.write(row_num, 2, vendor.total_invoices, cell_fmt)
        ws.write(row_num, 3, vendor.matched, cell_fmt)
        ws.write(row_num, 4, vendor.missing_in_2b, cell_fmt)
        ws.write(row_num, 5, vendor.missing_in_books, cell_fmt)
        ws.write(row_num, 6, vendor.tax_mismatch, cell_fmt)
        ws.write(row_num, 7, float(vendor.itc_available or 0), money_fmt)
        ws.write(row_num, 8, float(vendor.itc_at_risk or 0), money_fmt)
