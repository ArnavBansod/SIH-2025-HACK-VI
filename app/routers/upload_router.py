from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import pandas as pd
from ..utils import read_tabular_file, normalize_columns
from ..schemas import UploadResponse, StudentRecordIn, StudentCreate
from ..database import get_db
from .. import crud
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from ..auth import get_current_user
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/files", response_model=UploadResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    token_data = Depends(get_current_user)
):
    """
    Accept multiple files (attendance/test/fees) and process them.
    This endpoint expects files to contain a 'student_id' column (case-insensitive).
    It will parse each file and insert/update student records accordingly.
    """
    processed = 0
    for file in files:
        # reading (blocking) in threadpool
        df = await run_in_threadpool(read_tabular_file, file)
        df = normalize_columns(df)
        if "student_id" not in df.columns:
            raise HTTPException(status_code=422, detail=f"File {file.filename} must contain 'student_id' column")
        # iterate rows and push records
        for _, row in df.iterrows():
            # safe extraction with defaults
            student_payload = StudentCreate(student_id=str(row.get("student_id")), name=row.get("name"))
            await crud.create_or_update_student(db, student_payload)
            rec = StudentRecordIn(
                student_id=str(row.get("student_id")),
                date=row.get("date") if "date" in df.columns else None,
                attendance=float(row.get("attendance")) if "attendance" in df.columns and pd.notna(row.get("attendance")) else None,
                test_score=float(row.get("test_score")) if "test_score" in df.columns and pd.notna(row.get("test_score")) else None,
                fee_paid=bool(row.get("fee_paid")) if "fee_paid" in df.columns else True,
                fee_due_date=row.get("fee_due_date") if "fee_due_date" in df.columns else None,
                attempts=int(row.get("attempts")) if "attempts" in df.columns and pd.notna(row.get("attempts")) else 0,
                additional={k: row[k] for k in df.columns if k not in {"student_id","name","date","attendance","test_score","fee_paid","fee_due_date","attempts"}}
            )
            await crud.add_student_record(db, rec)
            processed += 1
    return {"message": "files processed", "processed_records": processed}
