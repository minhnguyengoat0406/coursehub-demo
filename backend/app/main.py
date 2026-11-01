from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .database import engine
from .schemas import EnrollmentCreate


logger = logging.getLogger(__name__)

app = FastAPI(
    title="CourseHub API",
    version="0.4.0",
    description="API thuc hanh Buoi 4 - Transaction, Concurrency va Index",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "CourseHub API dang hoat dong"}


@app.get("/health")
def health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("Khong ket noi duoc co so du lieu")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong ket noi duoc co so du lieu",
        ) from exc

    return {"status": "ok", "database": "connected"}


@app.get("/courses")
def list_courses(
    q: str | None = Query(default=None, min_length=1),
) -> list[dict[str, object]]:
    sql = """
        SELECT code, name, credits
        FROM courses
    """

    parameters: dict[str, object] = {}

    if q is not None:
        keyword = q.strip().lower()

        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tu khoa tim kiem khong duoc rong",
            )

        sql += """
            WHERE LOWER(code) LIKE :keyword
               OR LOWER(name) LIKE :keyword
        """

        parameters["keyword"] = f"%{keyword}%"

    sql += " ORDER BY code"

    with engine.connect() as connection:
        rows = connection.execute(
            text(sql),
            parameters,
        ).mappings().all()

    return [dict(row) for row in rows]


@app.get("/courses/{course_code}")
def get_course(course_code: str) -> dict[str, object]:
    sql = """
        SELECT code, name, credits
        FROM courses
        WHERE code = :course_code
    """

    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"course_code": course_code.upper()},
        ).mappings().first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Khong tim thay hoc phan",
        )

    return dict(row)


@app.get("/sections")
def list_sections(
    available_only: bool = False,
) -> list[dict[str, object]]:
    sql = """
        SELECT class_id, course_code, capacity, enrolled, remaining
        FROM v_section_summary
    """

    if available_only:
        sql += " WHERE remaining > 0"

    sql += " ORDER BY class_id"

    with engine.connect() as connection:
        rows = connection.execute(
            text(sql)
        ).mappings().all()

    return [dict(row) for row in rows]


@app.get("/students/{student_id}/enrollments")
def list_student_enrollments(
    student_id: str,
) -> list[dict[str, object]]:

    student_sql = """
        SELECT id
        FROM students
        WHERE id = :student_id
    """

    enrollment_sql = """
        SELECT
            e.student_id,
            s.full_name AS student_name,
            cs.id AS class_section_id,
            c.code AS course_code,
            c.name AS course_name,
            e.registered_at
        FROM enrollments AS e
        JOIN students AS s
            ON s.id = e.student_id
        JOIN class_sections AS cs
            ON cs.id = e.class_section_id
        JOIN courses AS c
            ON c.code = cs.course_code
        WHERE e.student_id = :student_id
        ORDER BY cs.id
    """

    with engine.connect() as connection:
        student = connection.execute(
            text(student_sql),
            {"student_id": student_id},
        ).first()

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay sinh vien",
            )

        rows = connection.execute(
            text(enrollment_sql),
            {"student_id": student_id},
        ).mappings().all()

    return [dict(row) for row in rows]


@app.post(
    "/enrollments",
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    payload: EnrollmentCreate,
) -> dict[str, str]:

    student_sql = """
        SELECT id
        FROM students
        WHERE id = :student_id
    """

    # Khoa dong class_sections de tranh race condition.
    section_sql = """
        SELECT id, capacity
        FROM class_sections
        WHERE id = :class_section_id
        FOR UPDATE
    """

    duplicate_sql = """
        SELECT 1
        FROM enrollments
        WHERE student_id = :student_id
          AND class_section_id = :class_section_id
    """

    count_sql = """
        SELECT COUNT(*) AS enrolled
        FROM enrollments
        WHERE class_section_id = :class_section_id
    """

    insert_enrollment_sql = """
        INSERT INTO enrollments (
            student_id,
            class_section_id
        )
        VALUES (
            :student_id,
            :class_section_id
        )
    """

    insert_event_sql = """
        INSERT INTO enrollment_events (
            student_id,
            class_section_id,
            event_type,
            source,
            dataset
        )
        VALUES (
            :student_id,
            :class_section_id,
            'CREATED',
            'api',
            'demo'
        )
    """

    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

    # Toan bo qua trinh dang ky nam trong cung mot transaction.
    with engine.begin() as connection:

        student = connection.execute(
            text(student_sql),
            {"student_id": payload.student_id},
        ).first()

        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay sinh vien",
            )

        section = connection.execute(
            text(section_sql),
            {"class_section_id": payload.class_section_id},
        ).mappings().first()

        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay lop hoc phan",
            )

        duplicated = connection.execute(
            text(duplicate_sql),
            parameters,
        ).first()

        if duplicated is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sinh vien da dang ky lop nay",
            )

        count_row = connection.execute(
            text(count_sql),
            {"class_section_id": payload.class_section_id},
        ).mappings().first()

        enrolled = int(count_row["enrolled"])

        if enrolled >= int(section["capacity"]):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lop hoc phan da het cho",
            )

        # Buoc 1: tao enrollment.
        connection.execute(
            text(insert_enrollment_sql),
            parameters,
        )

        # Buoc 2: ghi audit event.
        # Neu buoc nay loi thi enrollment ben tren cung rollback.
        connection.execute(
            text(insert_event_sql),
            parameters,
        )

    return {
        "message": "Dang ky thanh cong",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }


@app.delete(
    "/enrollments/{student_id}/{class_section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(
    student_id: str,
    class_section_id: str,
) -> Response:

    delete_sql = """
        DELETE FROM enrollments
        WHERE student_id = :student_id
          AND class_section_id = :class_section_id
    """

    insert_event_sql = """
        INSERT INTO enrollment_events (
            student_id,
            class_section_id,
            event_type,
            source,
            dataset
        )
        VALUES (
            :student_id,
            :class_section_id,
            'CANCELLED',
            'api',
            'demo'
        )
    """

    parameters = {
        "student_id": student_id,
        "class_section_id": class_section_id,
    }

    # DELETE va audit event cung nam trong mot transaction.
    with engine.begin() as connection:

        result = connection.execute(
            text(delete_sql),
            parameters,
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay dang ky can huy",
            )

        connection.execute(
            text(insert_event_sql),
            parameters,
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )