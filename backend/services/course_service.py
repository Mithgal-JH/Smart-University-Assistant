from db.connection import SessionLocal
from db.models import Course
from sqlalchemy.orm import Session


def add_course(user_id, name, doctor, days, time):
    db = SessionLocal()
    try:
        # منع التكرار بالاسم (case-insensitive)
        name_normalized = name.strip()
        existing = db.query(Course).filter(
            Course.user_id == user_id,
            Course.name == name_normalized
        ).first()

        if existing:
            return False

        new_course = Course(
            user_id=user_id,
            name=name_normalized,
            doctor=doctor,
            days=days,
            time=time
        )

        db.add(new_course)
        db.commit()
        return True

    finally:
        db.close()  # يضمن إغلاق الاتصال حتى لو صار خطأ


def get_courses_by_user(user_id: int):
    db: Session = SessionLocal()
    try:
        return db.query(Course).filter(Course.user_id == user_id).all()
    finally:
        db.close()


def delete_course(course_id: int, user_id: int):
    db: Session = SessionLocal()
    try:
        course = db.query(Course).filter(
            Course.id == course_id,
            Course.user_id == user_id
        ).first()

        if not course:
            return False

        db.delete(course)
        db.commit()
        return True

    finally:
        db.close()