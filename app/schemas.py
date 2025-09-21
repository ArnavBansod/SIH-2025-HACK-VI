from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "mentor"

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegisterResponse(BaseModel):
    message: str
    username: str

class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role: str

    class Config:
        orm_mode = True

class StudentBase(BaseModel):
    student_id: str
    name: Optional[str]
    meta: Optional[Dict[str, Any]] = None

class StudentCreate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    created_at: datetime.datetime

    class Config:
        orm_mode = True

class StudentRecordIn(BaseModel):
    student_id: str
    date: Optional[datetime.date]
    attendance: Optional[float]
    test_score: Optional[float]
    fee_paid: Optional[bool] = True
    fee_due_date: Optional[datetime.date]
    attempts: Optional[int] = 0
    additional: Optional[Dict[str, Any]] = None

class PredictionOut(BaseModel):
    id: int
    student_id: int
    risk_score: float
    risk_label: str
    created_at: datetime.datetime
    details: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True

class UploadResponse(BaseModel):
    message: str
    processed_records: int
