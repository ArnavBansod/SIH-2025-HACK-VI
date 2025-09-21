from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Date
)
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(256), nullable=True)
    role = Column(String(50), default="mentor")  # mentor/admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(256), nullable=True)
    meta = Column(JSON, nullable=True)  # extra fields: course, year, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    records = relationship("StudentRecord", back_populates="student")

class StudentRecord(Base):
    __tablename__ = "student_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=True)
    attendance = Column(Float, nullable=True)  # percent
    test_score = Column(Float, nullable=True)
    fee_paid = Column(Boolean, default=True)
    fee_due_date = Column(Date, nullable=True)
    attempts = Column(Integer, default=0)
    additional = Column(JSON, nullable=True)  # any other data
    student = relationship("Student", back_populates="records")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_label = Column(String(32), nullable=False)  # e.g., 'low', 'medium', 'high'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(JSON, nullable=True)
