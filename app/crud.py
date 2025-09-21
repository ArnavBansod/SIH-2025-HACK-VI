from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import models
from .schemas import UserCreate, StudentCreate, StudentRecordIn
from typing import Optional, List
from sqlalchemy.exc import NoResultFound
import datetime

# User CRUD
async def create_user(db: AsyncSession, user: UserCreate, hashed_password: str) -> models.User:
    db_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    q = select(models.User).where(models.User.username == username).limit(1)
    res = await db.execute(q)
    return res.scalar_one_or_none()

# Students
async def get_student_by_student_id(db: AsyncSession, student_id: str) -> Optional[models.Student]:
    q = select(models.Student).where(models.Student.student_id==student_id).limit(1)
    res = await db.execute(q)
    return res.scalar_one_or_none()

async def create_or_update_student(db: AsyncSession, student: StudentCreate) -> models.Student:
    existing = await get_student_by_student_id(db, student.student_id)
    if existing:
        existing.name = student.name or existing.name
        existing.meta = student.meta or existing.meta
        db.add(existing)
        await db.commit()
        await db.refresh(existing)
        return existing
    new = models.Student(student_id=student.student_id, name=student.name, meta=student.meta)
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new

async def add_student_record(db: AsyncSession, record: StudentRecordIn) -> models.StudentRecord:
    student = await get_student_by_student_id(db, record.student_id)
    if not student:
        # create quick minimal student if not exists
        student = models.Student(student_id=record.student_id, name=None)
        db.add(student)
        await db.commit()
        await db.refresh(student)
    sr = models.StudentRecord(
        student_id=student.id,
        date=record.date,
        attendance=record.attendance,
        test_score=record.test_score,
        fee_paid=record.fee_paid,
        fee_due_date=record.fee_due_date,
        attempts=record.attempts,
        additional=record.additional,
    )
    db.add(sr)
    await db.commit()
    await db.refresh(sr)
    return sr

async def list_students(db: AsyncSession, limit: int = 100) -> List[models.Student]:
    q = select(models.Student).limit(limit)
    res = await db.execute(q)
    return res.scalars().all()

async def create_prediction(db: AsyncSession, student_id: int, risk_score: float, risk_label: str, details: dict) -> models.Prediction:
    p = models.Prediction(student_id=student_id, risk_score=risk_score, risk_label=risk_label, details=details)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p
