from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models import User, Course, Lesson
from app.schemas import CourseOut, LessonOut
from app.services.education_service import complete_lesson

router = APIRouter()


@router.get("/courses", response_model=list[CourseOut])
def get_courses(db: Session = Depends(get_db)):
    return db.scalars(select(Course).where(Course.is_published == True)).all()


@router.get("/courses/{course_id}/lessons", response_model=list[LessonOut])
def get_lessons(course_id: str, db: Session = Depends(get_db)):
    return db.scalars(
        select(Lesson)
        .where(Lesson.course_id == course_id)
        .order_by(Lesson.order_no)
    ).all()


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson_endpoint(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return complete_lesson(db=db, user_id=current_user.id, lesson_id=lesson_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
