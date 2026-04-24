from fastapi import APIRouter
from db.connection import SessionLocal
from db.models import User,Student

router = APIRouter()

@router.post("/create_user")
def create_user(email: str):
    db = SessionLocal()
    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
  
@router.post("/add_student")
def add_student(user_id: int, major: str, gpa: float):
    db = SessionLocal()

    student = Student(
        user_id=user_id,
        major=major,
        gpa=gpa
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return student