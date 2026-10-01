print("CourseHub - Buoi 1")

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

for course in courses:
    remaining = course["capacity"] - course["enrolled"]
    print(course["code"], "- con", remaining, "cho")


def find_course(course_code):
    for course in courses:
        if course["code"] == course_code:
            return course
    return None


def can_enroll(student_id, course_code):
    course = find_course(course_code)

    if course is None:
        return False, "Course not found"

    for item in enrollments:
        if item["student_id"] == student_id and item["course_code"] == course_code:
            return False, "Duplicate"

    if course["enrolled"] >= course["capacity"]:
        return False, "Full"

    return True, "Success"


try:
    limit = int(input("Limit: "))
    print(courses[:limit])
except ValueError:
    print("Fail")


def search_courses(keyword):
    keyword = keyword.strip().lower()
    results = []

    for course in courses:
        if keyword in course["code"].lower() or keyword in course["name"].lower():
            results.append(course)

    return results


def find_student(student_id):
    for student in students:
        if student["id"] == student_id:
            return student
    return None


def enroll_student(student_id, course_code):
    student = find_student(student_id)

    if student is None:
        return False, "Student not found"

    course = find_course(course_code)

    if course is None:
        return False, "Course not found"

    for item in enrollments:
        if item["student_id"] == student_id and item["course_code"] == course_code:
            return False, "Duplicate"

    if course["enrolled"] >= course["capacity"]:
        return False, "Full"

    enrollments.append({
        "student_id": student_id,
        "course_code": course_code
    })

    course["enrolled"] += 1

    return True, "Success"


print(enroll_student("22000002", "INT2204"))
print(enroll_student("22000002", "INT2204"))
print(enroll_student("22000001", "INT2205"))
print(enroll_student("22000001", "INT9999"))
print(enroll_student("99999999", "INT2204"))