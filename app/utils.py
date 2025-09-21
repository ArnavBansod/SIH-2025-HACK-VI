from fastapi import UploadFile, HTTPException
import pandas as pd
from typing import Tuple, Dict, Any
import io

ALLOWED_EXT = {"csv", "xls", "xlsx"}

def read_tabular_file(upload_file: UploadFile) -> pd.DataFrame:
    """Read a CSV/XLS/XLSX file into pandas DataFrame"""
    filename = upload_file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="File without name uploaded")
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file extension")
    contents = upload_file.file.read()
    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(contents))
        else:
            # pandas can read excel from bytes buffer
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {e}")
    finally:
        upload_file.file.close()
    return df

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip column names to simplify mapping."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df
