import os
import pandas as pd
from fastapi import HTTPException


def parse_file_to_dataframe(filepath: str, max_rows: int) -> pd.DataFrame:
    """
    Parse an xlsx or csv file into a pandas DataFrame.
    Validates magic bytes, enforces row limit.
    """
    if not os.path.exists(filepath):
        raise HTTPException(status_code=400, detail=f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    with open(filepath, "rb") as f:
        header = f.read(4)

    if ext == ".xlsx":
        if header[:4] != b"PK\x03\x04":
            raise ValueError("Invalid XLSX file: bad magic bytes")
        df = pd.read_excel(filepath, engine="openpyxl", nrows=max_rows + 1)
    elif ext == ".csv":
        try:
            header.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Invalid CSV: file is not UTF-8 encoded")
        df = pd.read_csv(filepath, nrows=max_rows + 1, dtype=str)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if len(df) > max_rows:
        raise ValueError(f"File exceeds maximum row limit of {max_rows}")

    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    # Drop fully empty rows
    df = df.dropna(how="all")

    return df
