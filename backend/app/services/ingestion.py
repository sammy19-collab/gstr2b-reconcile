import os
import pandas as pd
import openpyxl

HEADER_KEYWORDS = [
    "invoice", "date", "gstin", "gst", "tax", "amount", "value",
    "vendor", "supplier", "party", "name", "number", "no", "vch",
    "particulars", "debit", "credit", "igst", "cgst", "sgst",
    "remark", "source", "irn", "cess", "place", "type", "rate",
]


def _row_header_score(row) -> int:
    score = 0
    for cell in row:
        if cell is None:
            continue
        s = str(cell).strip().lower()
        if not s or s == "nan":
            continue
        if isinstance(cell, (int, float)):
            continue
        try:
            float(str(cell).replace(",", ""))
            continue
        except ValueError:
            pass
        for kw in HEADER_KEYWORDS:
            if kw in s:
                score += 1
                break
    return score


def _find_best_sheet(filepath: str) -> str:
    """For multi-sheet workbooks, find the most data-rich sheet."""
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    sheets = wb.sheetnames

    # Prefer sheets with "b2b" or "purchase" in the name
    for name in sheets:
        nl = name.lower()
        if nl in ("b2b", "purchase register", "purchase", "gstr2b", "2b"):
            wb.close()
            return name

    # Fall back to sheet with most rows
    best_sheet = sheets[0]
    best_rows = 0
    for name in sheets:
        ws = wb[name]
        rows = ws.max_row or 0
        if rows > best_rows:
            best_rows = rows
            best_sheet = name
    wb.close()
    return best_sheet


def _find_header_row_in_sheet(filepath: str, sheet_name: str, max_scan: int = 15) -> int:
    """Find the header row index (0-based) within a sheet."""
    raw = pd.read_excel(filepath, engine="openpyxl", sheet_name=sheet_name,
                        header=None, nrows=max_scan)
    best_row = 0
    best_score = -1
    for i, row in raw.iterrows():
        vals = row.tolist()
        score = _row_header_score(vals)
        non_null = sum(1 for c in vals if c is not None and str(c).strip() and str(c).strip() != "nan")
        weighted = score * max(non_null, 1)
        if weighted > best_score:
            best_score = weighted
            best_row = int(i)
    return best_row


def _build_combined_columns(filepath: str, sheet_name: str, header_row: int) -> tuple[list[str], int]:
    """
    For files with two-row headers (e.g. GSTR-2B), combine them.
    Returns (column_names, data_start_row).
    """
    raw = pd.read_excel(filepath, engine="openpyxl", sheet_name=sheet_name,
                        header=None, nrows=header_row + 3)

    row1 = raw.iloc[header_row].tolist() if header_row < len(raw) else []
    row2 = raw.iloc[header_row + 1].tolist() if (header_row + 1) < len(raw) else []

    row2_score = _row_header_score(row2)
    row2_non_null = sum(1 for c in row2 if c is not None and str(c).strip() and str(c).strip() != "nan")

    if row2_score >= 2 and row2_non_null >= 2:
        # Fill forward row1 for merged cells
        filled = []
        last = ""
        for c in row1:
            cs = str(c).strip() if c is not None else ""
            if cs and cs != "nan":
                last = cs
            filled.append(last)

        combined = []
        for r1, r2 in zip(filled, row2):
            r2s = str(r2).strip() if r2 is not None else ""
            if r2s and r2s != "nan":
                combined.append(r2s)
            else:
                combined.append(r1)
        return combined, header_row + 2
    else:
        cols = [str(c).strip() if c is not None and str(c).strip() != "nan" else f"col_{i}"
                for i, c in enumerate(row1)]
        return cols, header_row + 1


def parse_file_to_dataframe(filepath: str, max_rows: int) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    with open(filepath, "rb") as f:
        magic = f.read(4)

    if ext == ".xlsx":
        if magic[:4] != b"PK\x03\x04":
            raise ValueError("Invalid XLSX file: bad magic bytes")

        sheet_name = _find_best_sheet(filepath)
        header_row = _find_header_row_in_sheet(filepath, sheet_name)
        col_names, data_start = _build_combined_columns(filepath, sheet_name, header_row)

        df = pd.read_excel(
            filepath, engine="openpyxl", sheet_name=sheet_name,
            header=None, skiprows=data_start, nrows=max_rows
        )
        # Assign column names (trim/pad as needed)
        ncols = min(len(col_names), len(df.columns))
        df = df.iloc[:, :ncols]
        df.columns = col_names[:ncols]

    elif ext == ".csv":
        try:
            magic.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Invalid CSV: not UTF-8 encoded")
        # For CSV just try to find header row
        raw = pd.read_csv(filepath, header=None, nrows=15, dtype=str)
        best_row = 0
        best_score = -1
        for i, row in raw.iterrows():
            score = _row_header_score(row.tolist())
            non_null = row.notna().sum()
            w = score * max(int(non_null), 1)
            if w > best_score:
                best_score = w
                best_row = int(i)
        df = pd.read_csv(filepath, skiprows=best_row, nrows=max_rows, dtype=str)
    else:
        raise ValueError(f"Unsupported format: {ext}")

    # Clean up
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")

    # Remove total/summary rows
    if len(df) > 0:
        first_col = df.columns[0]
        mask = df[first_col].astype(str).str.lower().str.strip().str.startswith("total")
        df = df[~mask]

    if len(df) > max_rows:
        raise ValueError(f"File exceeds maximum row limit of {max_rows}")

    return df.reset_index(drop=True)
