
# DỮ LIỆU MÔ PHỎNG (Lấy từ bài thực hành CourseHub)

students = [
    {"id": "22000001", "name": "Nguyen Minh Anh", "major": "KHDL"},
    {"id": "22000002", "name": "Tran Duc Long", "major": "KHDL"},
]

courses = [
    {
        "code": "INT2204",
        "name": "Co so du lieu Web va he thong thong tin",
        "capacity": 3,
        "enrolled": 2,
    },
    {
        "code": "INT2205",
        "name": "Khai pha du lieu",
        "capacity": 2,
        "enrolled": 2,
    },
]

enrollments = [
    {"student_id": "22000001", "course_code": "INT2204"}
]

# HÀM BỔ TRỢ TÌM KIẾM
def find_student(student_id):
    for student in students:
        if student["id"] == student_id:
            return student
    return None

def find_course(course_code):
    for course in courses:
        if course["code"] == course_code:
            return course
    return None

# VII.1: HÀM ĐĂNG KÝ HỌC PHẦN (ENROLL_STUDENT)
def enroll_student(student_id, course_code):
    # 1. Kiểm tra sinh viên tồn tại
    student = find_student(student_id)
    if student is None:
        return False, "Ma sinh vien khong ton tai"

    # 2. Kiểm tra học phần tồn tại
    course = find_course(course_code)
    if course is None:
        return False, "Ma hoc phan khong ton tai"

    # 3. Kiểm tra lớp học phần còn chỗ
    if course["enrolled"] >= course["capacity"]:
        return False, "Lop da du so luong"

    # 4. Kiểm tra sinh viên chưa đăng ký trùng
    is_duplicated = any(
        item["student_id"] == student_id and item["course_code"] == course_code
        for item in enrollments
    )
    if is_duplicated:
        return False, "Sinh vien da dang ky hoc phan nay"

    # 5. Nếu thỏa mãn: Thêm bản ghi và tăng số lượng đã đăng ký
    enrollments.append({"student_id": student_id, "course_code": course_code})
    course["enrolled"] += 1
    return True, "Dang ky thanh cong"


# VII.2: TẠO 05 TÌNH HUỐNG CHẠY THỬ (TEST CASES)
print("=== KẾT QUẢ KIỂM THỬ THỰC HÀNH PHẦN VII ===")

# Case 1: Đăng ký thành công (Sinh viên 22000002 đăng ký INT2204)
status, msg = enroll_student("22000002", "INT2204")
print(f"Case 1 (Thanh cong): Status={status} | Msg={msg}")

# Case 2: Đăng ký trùng (Sinh viên 22000001 đã đăng ký INT2204 từ trước)
status, msg = enroll_student("22000001", "INT2204")
print(f"Case 2 (Dang ky trung): Status={status} | Msg={msg}")

# Case 3: Lớp đầy (Lớp INT2205 đã có enrolled=2, capacity=2)
status, msg = enroll_student("22000001", "INT2205")
print(f"Case 3 (Lop day): Status={status} | Msg={msg}")

# Case 4: Mã học phần không tồn tại
status, msg = enroll_student("22000001", "INT9999")
print(f"Case 4 (Hoc phan khong ton tai): Status={status} | Msg={msg}")

# Case 5: Mã sinh viên không tồn tại
status, msg = enroll_student("99999999", "INT2204")
print(f"Case 5 (Sinh vien khong ton tai): Status={status} | Msg={msg}")