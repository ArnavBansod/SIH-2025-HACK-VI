from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from .. import crud
from ..auth import get_current_user, ensure_role
from ..schemas import PredictionOut, StudentOut
from typing import List
import pandas as pd
from ..ml_pipeline import predict_risk, feature_engineer
from sqlalchemy import select
from .. import models
import datetime

router = APIRouter(prefix="/students", tags=["students"])

@router.get("/", response_model=List[StudentOut])
async def list_students(limit: int = Query(100, ge=1, le=1000), db: AsyncSession = Depends(get_db), token=Depends(get_current_user)):
    # Ensure only mentors/admins can list
    ensure_role(token, ["mentor", "admin"])
    students = await crud.list_students(db, limit=limit)
    return students

@router.get("/predict", response_model=List[PredictionOut])
async def generate_predictions(db: AsyncSession = Depends(get_db), token=Depends(get_current_user)):
    """
    Pull latest records, create a merged DataFrame keyed by student_id, and run prediction.
    Saves predictions to DB and returns them.
    """
    ensure_role(token, ["mentor", "admin"])
    # Query latest student records - for simplicity, get latest record per student
    q = select(models.Student, models.StudentRecord).join(models.StudentRecord, models.Student.id==models.StudentRecord.student_id)
    res = await db.execute(q)
    rows = res.all()
    if not rows:
        return []
    # Build DataFrame
    data = []
    for student, record in rows:
        data.append({
            "student_id": student.student_id,
            "name": student.name,
            "attendance": record.attendance,
            "test_score": record.test_score,
            "attempts": record.attempts,
            "fee_paid": record.fee_paid,
            "fee_due_date": record.fee_due_date,
            # compute days past due
            "days_past_due": (datetime.date.today() - record.fee_due_date).days if record.fee_due_date else 0
        })
    df = pd.DataFrame(data)
    if df.empty:
        return []
    preds_df = predict_risk(df)
    results = []
    for _, pred in preds_df.iterrows():
        # find student internal id
        s = await crud.get_student_by_student_id(db, pred["student_id"])
        if not s:
            continue
        p = await crud.create_prediction(db, s.id, float(pred["risk_score"]), pred["risk_label"], pred["details"])
        results.append(p)
    return results
