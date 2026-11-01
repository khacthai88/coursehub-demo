from __future__ import annotations
import logging
from fastapi import FastAPI, HTTPException, Query, Response, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .database import engine
from .schemas import EnrollmentCreate, SectionCapacityUpdate

logger = logging.getLogger(__name__)

app = FastAPI(
    title="CourseHub API",
    version="0.4.0",
    description="API thuc hanh Buoi 4 - transaction, locking va hieu nang",
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
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100)
) -> list[dict[str, object]]:
    sql = "SELECT code, name, credits FROM courses"
    parameters: dict[str, object] = {}

    if q is not None:
        keyword = q.strip().lower()
        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tu khoa tim kiem khong duoc rong"
            )
        sql += " WHERE LOWER(code) LIKE :keyword OR LOWER(name) LIKE :keyword"
        parameters["keyword"] = f"%{keyword}%"

    sql += " ORDER BY code OFFSET :skip LIMIT :limit"
    parameters["skip"] = skip
    parameters["limit"] = limit

    with engine.connect() as connection:
        rows = connection.execute(text(sql), parameters).mappings().all()
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
        rows = connection.execute(text(sql)).mappings().all()
        return [dict(row) for row in rows]

@app.get("/students/{student_id}/enrollments")
def list_student_enrollments(student_id: str) -> list[dict[str, object]]:
    student_sql = "SELECT id FROM students WHERE id = :student_id"
    enrollment_sql = """
    SELECT e.student_id,
           s.name AS student_name,
           cs.id AS class_section_id,
           c.code AS course_code,
           c.name AS course_name,
           e.registered_at
    FROM enrollments AS e
    JOIN students AS s ON s.id = e.student_id
    JOIN class_sections AS cs ON cs.id = e.class_section_id
    JOIN courses AS c ON c.code = cs.course_code
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

# --- V.2 & V.3: THAY TOÀN BỘ HÀM POST /enrollments (SỬ DỤNG ROW LOCK FOR UPDATE) ---
@app.post(
    "/enrollments",
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(payload: EnrollmentCreate) -> dict[str, str]:
    student_sql = "SELECT id FROM students WHERE id = :student_id"
    lock_section_sql = """
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
    SELECT COUNT(*)
    FROM enrollments
    WHERE class_section_id = :class_section_id
    """
    insert_sql = """
    INSERT INTO enrollments (student_id, class_section_id)
    VALUES (:student_id, :class_section_id)
    """
    event_sql = """
    INSERT INTO enrollment_events
    (student_id, class_section_id, event_type, source, dataset)
    VALUES
    (:student_id, :class_section_id, 'CREATED', 'api', 'demo')
    """

    parameters = {
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

    try:
        with engine.begin() as connection:
            # 1. Kiểm tra sinh viên
            student = connection.execute(
                text(student_sql),
                {"student_id": payload.student_id},
            ).first()
            if student is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay sinh vien",
                )

            # 2. Khóa dòng lớp học phần (Row Lock)
            section = connection.execute(
                text(lock_section_sql),
                {"class_section_id": payload.class_section_id},
            ).mappings().first()
            if section is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay lop hoc phan",
                )

            # 3. Kiểm tra đăng ký trùng
            duplicated = connection.execute(
                text(duplicate_sql), parameters
            ).first()
            if duplicated is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Sinh vien da dang ky lop nay",
                )

            # 4. Đếm số lượng sinh viên đã đăng ký
            enrolled = connection.execute(
                text(count_sql),
                {"class_section_id": payload.class_section_id},
            ).scalar_one()

            # 5. Kiểm tra sức chứa
            if int(enrolled) >= int(section["capacity"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Lop hoc phan da het cho",
                )

            # 6. Thêm đăng ký & Ghi audit event
            connection.execute(text(insert_sql), parameters)
            connection.execute(text(event_sql), parameters)

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dang ky xung dot voi du lieu hien tai",
        ) from exc

    return {
        "message": "Dang ky thanh cong",
        "student_id": payload.student_id,
        "class_section_id": payload.class_section_id,
    }

# --- V.4: THAY TOÀN BỘ HÀM DELETE /enrollments (SỬ DỤNG ROW LOCK & GHI EVENT CANCELLED) ---
@app.delete(
    "/enrollments/{student_id}/{class_section_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(student_id: str, class_section_id: str) -> Response:
    lock_section_sql = """
    SELECT id
    FROM class_sections
    WHERE id = :class_section_id
    FOR UPDATE
    """
    delete_sql = """
    DELETE FROM enrollments
    WHERE student_id = :student_id
      AND class_section_id = :class_section_id
    RETURNING student_id
    """
    event_sql = """
    INSERT INTO enrollment_events
    (student_id, class_section_id, event_type, source, dataset)
    VALUES
    (:student_id, :class_section_id, 'CANCELLED', 'api', 'demo')
    """
    parameters = {
        "student_id": student_id,
        "class_section_id": class_section_id,
    }

    try:
        with engine.begin() as connection:
            # 1. Khóa dòng lớp học phần (Row Lock) để đồng bộ với POST
            section = connection.execute(
                text(lock_section_sql),
                {"class_section_id": class_section_id},
            ).first()
            if section is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay lop hoc phan",
                )

            # 2. Xóa bản ghi đăng ký trong bảng enrollments
            deleted = connection.execute(
                text(delete_sql), parameters
            ).first()
            if deleted is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Khong tim thay dang ky can huy",
                )

            # 3. Ghi sự kiện audit 'CANCELLED' vào bảng enrollment_events
            connection.execute(text(event_sql), parameters)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loi he thong khi huy dang ky",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# --- BÀI 1: API DANH SÁCH GIẢNG VIÊN ---
@app.get("/lecturers")
def list_lecturers() -> list[dict[str, object]]:
    sql = "SELECT id, name FROM lecturers ORDER BY id"
    with engine.connect() as connection:
        rows = connection.execute(text(sql)).mappings().all()
        return [dict(row) for row in rows]

# --- BÀI 2: API CHI TIẾT MỘT LỚP HỌC PHẦN ---
@app.get("/sections/{section_id}")
def get_section_detail(section_id: str) -> dict[str, object]:
    sql = """
    SELECT 
        cs.id AS class_id,
        cs.course_code,
        c.name AS course_name,
        cs.semester_code AS semester,
        l.name AS lecturer_name,
        v.capacity,
        v.enrolled,
        v.remaining
    FROM class_sections cs
    JOIN courses c ON cs.course_code = c.code
    LEFT JOIN lecturers l ON cs.lecturer_id = l.id
    JOIN v_section_summary v ON cs.id = v.class_id
    WHERE cs.id = :section_id
    """
    with engine.connect() as connection:
        row = connection.execute(text(sql), {"section_id": section_id.upper()}).mappings().first()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay lop hoc phan"
            )
        return dict(row)

# --- BÀI 3: CẬP NHẬT SỨC CHỨA BẰNG PATCH ---
@app.patch("/sections/{section_id}/capacity")
def update_section_capacity(section_id: str, payload: SectionCapacityUpdate) -> dict[str, object]:
    section_id = section_id.upper()
    
    check_sql = """
    SELECT capacity, enrolled 
    FROM v_section_summary 
    WHERE class_id = :section_id
    """
    
    update_sql = """
    UPDATE class_sections 
    SET capacity = :new_capacity 
    WHERE id = :section_id
    """
    
    with engine.begin() as connection:
        current = connection.execute(text(check_sql), {"section_id": section_id}).mappings().first()
        
        if current is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay lop hoc phan"
            )
            
        if payload.capacity < current["enrolled"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Suc chua moi ({payload.capacity}) khong duoc nho hon so luong sinh vien da dang ky ({current['enrolled']})"
            )
            
        connection.execute(
            text(update_sql), 
            {"new_capacity": payload.capacity, "section_id": section_id}
        )
        
        return {
            "message": "Cap nhat suc chua thanh cong",
            "class_id": section_id,
            "new_capacity": payload.capacity
        }