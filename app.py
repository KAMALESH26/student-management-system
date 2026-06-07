from flask import Flask, render_template, request, redirect, session 
import pymysql

from flask import send_file
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "student_management_secret"


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = pymysql.connect(
            host="localhost",
            user="sms_user",
            password="sms123",
            database="student_management"
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=%s
            AND password=%s
            """,
            (username, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:

            session["user"] = username

            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/login")

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

        # Total Students

    cursor.execute(
        "SELECT COUNT(*) FROM students"
    )

    total_students = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            department,
            COUNT(*)

        FROM students

        GROUP BY department
    """)

    department_data = cursor.fetchall()

    # Total Departments

    cursor.execute(
        "SELECT COUNT(DISTINCT department) FROM students"
    )

    total_departments = cursor.fetchone()[0]


    # Final Year Students

    cursor.execute(
        "SELECT COUNT(*) FROM students WHERE year = 3"
    )

    final_year_students = cursor.fetchone()[0]

    # Average Attendance Percentage

    cursor.execute("""
        SELECT ROUND(
            AVG(
                CASE
                    WHEN status = 'Present'
                    THEN 100
                    ELSE 0
                END
            ),
            2
        )
        FROM attendance
    """)

    average_attendance = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT ROUND(AVG(marks),2)
        FROM marks
    """)

    class_average_marks = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT
            students.name,
            ROUND(AVG(marks.marks),2)

        FROM marks

        JOIN students
        ON marks.student_id = students.id

        GROUP BY students.name

        ORDER BY AVG(marks.marks) DESC

        LIMIT 5
    """)

    top_students = cursor.fetchall()

    search = request.args.get("search")

    if search:

        cursor.execute("""
            SELECT *
            FROM students
            WHERE
                name LIKE %s
                OR reg_no LIKE %s
                OR department LIKE %s
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()

    connection.close()

    return render_template(
        "students.html",
        students=students,
        total_students=total_students,
        total_departments=total_departments,
        final_year_students=final_year_students,
        average_attendance=average_attendance,
        top_students=top_students,
        department_data=department_data,
        class_average_marks=class_average_marks,
    )

@app.route("/marks", methods=["GET", "POST"])
def marks():

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    if request.method == "POST":

        student_id = request.form["student_id"]
        subject = request.form["subject"]
        marks = request.form["marks"]

        cursor.execute("""
            INSERT INTO marks
            (student_id, subject, marks)
            VALUES (%s, %s, %s)
        """, (
            student_id,
            subject,
            marks
        ))

        connection.commit()

    cursor.execute(
        "SELECT * FROM students"
    )

    students = cursor.fetchall()

    cursor.execute("""
        SELECT
            students.name,
            marks.subject,
            marks.marks

        FROM marks

        JOIN students
        ON marks.student_id = students.id

        ORDER BY marks.mark_id DESC

        LIMIT 10
    """)

    recent_marks = cursor.fetchall()

    connection.close()

    return render_template(
        "marks.html",
        students=students,
        recent_marks=recent_marks,
    )

@app.route("/marks-report")
def marks_report():

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            students.name,
            ROUND(AVG(marks.marks),2)

        FROM marks

        JOIN students
        ON marks.student_id = students.id

        GROUP BY students.name

        ORDER BY AVG(marks.marks) DESC
    """)

    report = cursor.fetchall()

    # Top Scorer

    top_scorer = report[0] if report else None

    # Class Average

    cursor.execute("""
        SELECT
            ROUND(AVG(marks),2)
        FROM marks
    """)

    class_average = cursor.fetchone()[0]

    students_evaluated = len(report)

    connection.close()

    return render_template(
        "marks_report.html",
        report=report,
        top_scorer=top_scorer,
        class_average=class_average,
        students_evaluated=students_evaluated
    )

@app.route("/results")
def results():

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            students.name,
            ROUND(AVG(marks.marks), 2) AS average_marks

        FROM marks

        JOIN students
        ON marks.student_id = students.id

        GROUP BY students.name

        ORDER BY average_marks DESC
    """)

    results = cursor.fetchall()

    # Top Scorer
    top_scorer = results[0] if results else None

    # Class Average
    cursor.execute("""
        SELECT ROUND(AVG(marks),2)
        FROM marks
    """)

    class_average = cursor.fetchone()[0]

    # Students Evaluated
    cursor.execute("""
        SELECT COUNT(DISTINCT student_id)
        FROM marks
    """)

    students_evaluated = cursor.fetchone()[0]

    connection.close()

    return render_template(
        "results.html",
        results=results,
        top_scorer=top_scorer,
        class_average=class_average,
        students_evaluated=students_evaluated
    )

@app.route("/attendance", methods=["GET", "POST"])
def attendance():

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    if request.method == "POST":

        student_id = request.form["student_id"]
        attendance_date = request.form["attendance_date"]
        status = request.form["status"]

        cursor.execute("""
            INSERT INTO attendance
            (student_id, attendance_date, status)
            VALUES (%s, %s, %s)
        """, (
            student_id,
            attendance_date,
            status
        ))

        connection.commit()

    cursor.execute(
        "SELECT * FROM students"
    )

    students = cursor.fetchall()

    cursor.execute("""
            SELECT
                students.name,
                attendance.attendance_date,
                attendance.status
            FROM attendance
            JOIN students
            ON attendance.student_id = students.id
            ORDER BY attendance.attendance_date DESC
    """)

    attendance_records = cursor.fetchall()

    connection.close()

    return render_template(
        "attendance.html",
        students=students,
        attendance_records=attendance_records
    )
    

@app.route("/add", methods=["GET", "POST"])
def add_student():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        reg_no = request.form["reg_no"]
        name = request.form["name"]
        department = request.form["department"]
        year = request.form["year"]
        email = request.form["email"]
        phone = request.form["phone"]

        connection = pymysql.connect(
            host="localhost",
            user="sms_user",
            password="sms123",
            database="student_management"
        )

        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO students
            (reg_no, name, department, year, email, phone)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            reg_no,
            name,
            department,
            year,
            email,
            phone
        ))

        connection.commit()
        connection.close()

        return redirect("/")

    return render_template("add_student.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_student(id):

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    if request.method == "POST":

        reg_no = request.form["reg_no"]
        name = request.form["name"]
        department = request.form["department"]
        year = request.form["year"]
        email = request.form["email"]
        phone = request.form["phone"]

        cursor.execute("""
            UPDATE students
            SET reg_no=%s,
                name=%s,
                department=%s,
                year=%s,
                email=%s,
                phone=%s
            WHERE id=%s
        """, (
            reg_no,
            name,
            department,
            year,
            email,
            phone,
            id
        ))

        connection.commit()
        connection.close()

        return redirect("/")

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cursor.fetchone()

    connection.close()

    return render_template(
        "edit_student.html",
        student=student
    )

@app.route("/delete/<int:id>")
def delete_student(id):
    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM students WHERE id=%s",
        (id,)
    )

    connection.commit()
    connection.close()

    return redirect("/")

@app.route("/attendance-report")
def attendance_report():

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            students.name,

            SUM(
                CASE
                    WHEN attendance.status='Present'
                    THEN 1
                    ELSE 0
                END
            ) AS present_days,

            COUNT(*) AS total_days,

            ROUND(
                (
                    SUM(
                        CASE
                            WHEN attendance.status='Present'
                            THEN 1
                            ELSE 0
                        END
                    ) * 100.0
                ) / COUNT(*),
                2
            ) AS percentage

        FROM attendance

        JOIN students
        ON attendance.student_id = students.id

        GROUP BY students.name

        ORDER BY percentage DESC
    """)

    report = cursor.fetchall()

    connection.close()

    return render_template(
        "attendance_report.html",
        report=report
    )    

@app.route("/student/<int:id>")
def student_profile(id):

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    # Student Details

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cursor.fetchone()

    # Attendance %

    cursor.execute("""
        SELECT
            ROUND(
                (
                    SUM(
                        CASE
                            WHEN status='Present'
                            THEN 1
                            ELSE 0
                        END
                    ) * 100.0
                ) / COUNT(*),
                2
            )
        FROM attendance
        WHERE student_id=%s
    """, (id,))

    attendance_percentage = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status='Absent' THEN 1 ELSE 0 END)
        FROM attendance
        WHERE student_id=%s
    """, (id,))

    attendance_counts = cursor.fetchone()

    present_count = attendance_counts[0] or 0
    absent_count = attendance_counts[1] or 0

    # Average Marks

    cursor.execute("""
        SELECT
            ROUND(AVG(marks),2)
        FROM marks
        WHERE student_id=%s
    """, (id,))

    average_marks = cursor.fetchone()[0]

    # Subject Marks

    cursor.execute("""
        SELECT
            subject,
            marks
        FROM marks
        WHERE student_id=%s
    """, (id,))

    marks_data = cursor.fetchall()
    total_subjects = len(marks_data)

    subjects = [row[0] for row in marks_data]
    marks_values = [row[1] for row in marks_data]

    connection.close()

    return render_template(
        "student_profile.html",
        student=student,
        attendance_percentage=attendance_percentage,
        average_marks=average_marks,
        marks_data=marks_data,
        subjects=subjects,
        marks_values=marks_values,
        present_count=present_count,
        absent_count=absent_count,
        total_subjects=total_subjects,
    )

@app.route("/student/<int:id>/pdf")
def student_pdf(id):

    if "user" not in session:
        return redirect("/login")

    connection = pymysql.connect(
        host="localhost",
        user="sms_user",
        password="sms123",
        database="student_management"
    )

    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (id,)
    )

    student = cursor.fetchone()

    cursor.execute("""
        SELECT
            ROUND(AVG(marks),2)
        FROM marks
        WHERE student_id=%s
    """, (id,))

    average_marks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            subject,
            marks
        FROM marks
        WHERE student_id=%s
    """, (id,))

    marks_data = cursor.fetchall()

    pdf_file = f"student_{id}.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "Student Report",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            f"Name: {student[2]}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Register No: {student[1]}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Department: {student[3]}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Average Marks: {average_marks}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            "Subject Marks",
            styles["Heading2"]
        )
    )

    for mark in marks_data:

        content.append(
            Paragraph(
                f"{mark[0]} : {mark[1]}",
                styles["Normal"]
            )
        )

    doc.build(content)

    connection.close()

    return send_file(
        pdf_file,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(debug=True)