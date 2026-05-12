from fastapi import APIRouter, Depends, HTTPException

from services.firebase_auth import verify_firebase_token
from services.course_service import get_courses_by_user, delete_course
from services.user_service import get_student_data

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/courses")
def me_list_courses(uid: str = Depends(verify_firebase_token)):
    courses = get_courses_by_user(uid)
    return [
        {
            "id": c.id,
            "name": c.name,
            "doctor": c.doctor,
            "days": c.days,
            "time": c.time,
        }
        for c in courses
    ]


@router.delete("/courses/{course_id}")
def me_delete_course(course_id: int, uid: str = Depends(verify_firebase_token)):
    if not delete_course(course_id, uid):
        raise HTTPException(status_code=404, detail="المادة غير موجودة أو لا تملك صلاحية حذفها.")
    return {"message": "تم حذف المادة بنجاح ✅"}


@router.get("/student")
def me_student(uid: str = Depends(verify_firebase_token)):
    student = get_student_data(uid)
    return {"student": student}
