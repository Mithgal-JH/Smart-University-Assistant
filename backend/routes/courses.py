from fastapi import APIRouter
from services.course_service import get_courses_by_user, delete_course

router = APIRouter()


# GET courses
@router.get("/courses")
def get_courses(user_id: int):
    courses = get_courses_by_user(user_id)

    return [
        {
            "id": c.id,
            "name": c.name,
            "doctor": c.doctor,
            "days": c.days,
            "time": c.time
        }
        for c in courses
    ]


# DELETE course
@router.delete("/courses/{course_id}")
def remove_course(course_id: int, user_id: int):
    success = delete_course(course_id, user_id)

    if not success:
        return {"message": "المادة غير موجودة"}

    return {"message": "تم حذف المادة بنجاح ✅"}