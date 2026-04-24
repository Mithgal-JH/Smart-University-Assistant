from db.connection import SessionLocal
from db.models import Student


def get_student_data(user_id: int):
    db = SessionLocal()
    try:
        student = db.query(Student).filter(Student.user_id == user_id).first()

        if not student:
            return None

        return {
            "major": student.major,
            "gpa": student.gpa
        }
    finally:
        db.close()