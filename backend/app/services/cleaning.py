import re
from typing import Optional
import pandas as pd
import numpy as np


def norm_invoice(value: Optional[str]) -> str:
    """Normalize invoice number: uppercase, strip spaces/special chars."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    s = str(value).strip().upper()
    # Remove spaces and common separators
    s = re.sub(r"[\s\-/\\]", "", s)
    return s


def norm_gstin(value: Optional[str]) -> str:
    """Normalize GSTIN: uppercase, strip whitespace."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value).strip().upper()


def norm_vendor(value: Optional[str]) -> str:
    """Normalize vendor name: uppercase, strip extra whitespace."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    s = str(value).strip().upper()
    s = re.sub(r"\s+", " ", s)
    # Remove common legal suffixes for better matching
    s = re.sub(r"\b(PVT|LTD|PRIVATE|LIMITED|LLP|INC|CORP|CO)\b\.?", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_amount(value) -> Optional[float]:
    """Parse amount fields, handling commas and None."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    s = str(value).strip().replace(",", "").replace(" ", "")
    if s == "" or s == "-":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return None


def parse_date(value) -> Optional[pd.Timestamp]:
    """Parse date fields with multiple format attempts."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value
    s = str(value).strip()
    if not s or s.lower() in ("nat", "none", "null"):
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            pass
    try:
        return pd.to_datetime(s, infer_datetime_format=True, dayfirst=True)
    except Exception:
        return None


def clean_purchase_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize all key columns in a purchase register DataFrame."""
    df = df.copy().reset_index(drop=True)

    if "invoice_number" in df.columns:
        df["invoice_number_norm"] = df["invoice_number"].apply(norm_invoice)
    else:
        df["invoice_number_norm"] = ""

    if "supplier_gstin" in df.columns:
        df["supplier_gstin_norm"] = df["supplier_gstin"].apply(norm_gstin)
    else:
        df["supplier_gstin_norm"] = ""

    if "supplier_name" in df.columns:
        df["supplier_name_norm"] = df["supplier_name"].apply(norm_vendor)
    else:
        df["supplier_name_norm"] = ""

    for amt_col in ["taxable_amount", "igst", "cgst", "sgst", "total_tax"]:
        if amt_col in df.columns:
            df[amt_col] = df[amt_col].apply(parse_amount)
        else:
            df[amt_col] = 0.0

    # Compute total_tax if not present
    if "total_tax" not in df.columns or df["total_tax"].isna().all():
        df["total_tax"] = (
            df.get("igst", pd.Series(0, index=df.index)).fillna(0)
            + df.get("cgst", pd.Series(0, index=df.index)).fillna(0)
            + df.get("sgst", pd.Series(0, index=df.index)).fillna(0)
        )

    if "invoice_date" in df.columns:
        df["invoice_date"] = df["invoice_date"].apply(parse_date)
    else:
        df["invoice_date"] = None

    return df


def clean_gstr2b_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize all key columns in a GSTR-2B DataFrame."""
    df = df.copy().reset_index(drop=True)

    if "invoice_number" in df.columns:
        df["invoice_number_norm"] = df["invoice_number"].apply(norm_invoice)
    else:
        df["invoice_number_norm"] = ""

    if "supplier_gstin" in df.columns:
        df["supplier_gstin_norm"] = df["supplier_gstin"].apply(norm_gstin)
    else:
        df["supplier_gstin_norm"] = ""

    if "supplier_name" in df.columns:
        df["supplier_name_norm"] = df["supplier_name"].apply(norm_vendor)
    else:
        df["supplier_name_norm"] = ""

    for amt_col in ["taxable_amount", "igst", "cgst", "sgst", "total_tax"]:
        if amt_col in df.columns:
            df[amt_col] = df[amt_col].apply(parse_amount)
        else:
            df[amt_col] = 0.0

    if "total_tax" not in df.columns or df["total_tax"].isna().all():
        df["total_tax"] = (
            df.get("igst", pd.Series(0, index=df.index)).fillna(0)
            + df.get("cgst", pd.Series(0, index=df.index)).fillna(0)
            + df.get("sgst", pd.Series(0, index=df.index)).fillna(0)
        )

    if "invoice_date" in df.columns:
        df["invoice_date"] = df["invoice_date"].apply(parse_date)
    else:
        df["invoice_date"] = None

    return df
