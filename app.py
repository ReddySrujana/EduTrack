from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import config
from flask import session

app = Flask(__name__)
app.config.from_object(config)
# set secret key for session management
app.secret_key = "eduTrack1234qwerty"

# ---------------- DATABASE ---------------- #
# helper function to get database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")  
    return g.db

# close database connection after each request
@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# initialize database and create tables if they don't exist
def init_db():
    db = get_db()

    db.executescript('''
    CREATE TABLE IF NOT EXISTS Users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT CHECK(role IN ('student', 'instructor')) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        instructor_id INTEGER NOT NULL,
        FOREIGN KEY (instructor_id) REFERENCES Users(user_id)
    );

    CREATE TABLE IF NOT EXISTS Enrollments (
        student_id INTEGER,
        course_id INTEGER,
        PRIMARY KEY (student_id, course_id),
        FOREIGN KEY (student_id) REFERENCES Users(user_id),
        FOREIGN KEY (course_id) REFERENCES Courses(course_id)
    );

    CREATE TABLE IF NOT EXISTS Assignments (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        instructions TEXT,
        due_date DATE,
        FOREIGN KEY (course_id) REFERENCES Courses(course_id)
    );

    CREATE TABLE IF NOT EXISTS Submissions (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id INTEGER,
        student_id INTEGER,
        submission_date DATE,
        answer TEXT,
        grade INTEGER,
        FOREIGN KEY (assignment_id) REFERENCES Assignments(assignment_id),
        FOREIGN KEY (student_id) REFERENCES Users(user_id)
    );
    ''')

    db.commit()

# ---------------- HOME ---------------- #
# home page
@app.route('/')
def index():
    return render_template('index.html')


# ---------------- USERS ---------------- #
# add user (student or instructor)
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']

        db = get_db()
        db.execute(
            'INSERT INTO Users (name, email, role) VALUES (?, ?, ?)',
            (name, email, role)
        )
        db.commit()
        return redirect(url_for('list_users'))

    return render_template('add_user.html')

# list all users with name, email, and role
@app.route('/users')
def list_users():
    db = get_db()
    users = db.execute('SELECT * FROM Users').fetchall()
    return render_template('list_users.html', users=users)

# edit user information (name, email, role)
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    db = get_db()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']

        try:
            db.execute('''
                UPDATE Users
                SET name = ?, email = ?, role = ?
                WHERE user_id = ?
            ''', (name, email, role, user_id))

            db.commit()

        except Exception as e:
            return f"Update failed: {e}"

        return redirect(url_for('list_users'))

    user = db.execute(
        'SELECT * FROM Users WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    return render_template('edit_user.html', user=user)

# delete user
@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    db = get_db()

    try:
        # delete submissions by this user
        db.execute('DELETE FROM Submissions WHERE student_id = ?', (user_id,))

        # delete enrollments
        db.execute('DELETE FROM Enrollments WHERE student_id = ?', (user_id,))

        # delete courses they teach
        db.execute('DELETE FROM Courses WHERE instructor_id = ?', (user_id,))

        # NOW delete the user
        db.execute('DELETE FROM Users WHERE user_id = ?', (user_id,))

        db.commit()

    except Exception as e:
        return f"Error: {e}"

    return redirect(url_for('list_users'))

# ---------------- COURSES ---------------- #
# add course
@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    db = get_db()

    if request.method == 'POST':
        course_name = request.form['course_name']
        instructor_id = request.form['instructor_id']

        db.execute(
            'INSERT INTO Courses (course_name, instructor_id) VALUES (?, ?)',
            (course_name, instructor_id)
        )
        db.commit()
        return redirect(url_for('list_courses'))

    instructors = db.execute(
        "SELECT * FROM Users WHERE role='instructor'"
    ).fetchall()

    return render_template('add_course.html', instructors=instructors)

# list all courses with course name and instructor name
@app.route('/courses')
def list_courses():
    db = get_db()
    courses = db.execute('''
        SELECT c.course_id, c.course_name, u.name AS instructor
        FROM Courses c
        JOIN Users u ON c.instructor_id = u.user_id
    ''').fetchall()

    return render_template('list_courses.html', courses=courses)

# edit course information (course name and instructor)
@app.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    db = get_db()

    if request.method == 'POST':
        course_name = request.form['course_name']
        instructor_id = request.form['instructor_id']

        db.execute('''
            UPDATE Courses
            SET course_name = ?, instructor_id = ?
            WHERE course_id = ?
        ''', (course_name, instructor_id, course_id))

        db.commit()
        return redirect(url_for('list_courses'))

    course = db.execute(
        'SELECT * FROM Courses WHERE course_id = ?',
        (course_id,)
    ).fetchone()

    instructors = db.execute(
        "SELECT * FROM Users WHERE role='instructor'"
    ).fetchall()

    return render_template(
        'edit_course.html',
        course=course,
        instructors=instructors
    )

# Delete Course
@app.route('/delete_course/<int:course_id>')
def delete_course(course_id):
    db = get_db()

    try:
        # delete submissions linked to assignments in this course
        db.execute('''
            DELETE FROM Submissions
            WHERE assignment_id IN (
                SELECT assignment_id FROM Assignments WHERE course_id = ?
            )
        ''', (course_id,))

        # delete assignments
        db.execute('DELETE FROM Assignments WHERE course_id = ?', (course_id,))

        # delete enrollments
        db.execute('DELETE FROM Enrollments WHERE course_id = ?', (course_id,))

        # delete course
        db.execute('DELETE FROM Courses WHERE course_id = ?', (course_id,))

        db.commit()

    except Exception as e:
        return f"Error: {e}"

    return redirect(url_for('list_courses'))

# ---------------- ENROLLMENTS ---------------- #

# enroll student in course
@app.route('/enroll', methods=['GET', 'POST'])
def enroll():
    db = get_db()

    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id = request.form['course_id']

        db.execute(
            'INSERT INTO Enrollments (student_id, course_id) VALUES (?, ?)',
            (student_id, course_id)
        )
        db.commit()
        return redirect(url_for('list_enrollments'))

    students = db.execute(
        "SELECT * FROM Users WHERE role='student'"
    ).fetchall()

    courses = db.execute("SELECT * FROM Courses").fetchall()

    return render_template('enroll.html', students=students, courses=courses)

# list all enrollments with student name and course name
@app.route('/enrollments')
def list_enrollments():
    db = get_db()

    enrollments = db.execute('''
        SELECT 
            e.student_id,
            e.course_id,
            u.name AS student,
            c.course_name
        FROM Enrollments e
        JOIN Users u ON e.student_id = u.user_id
        JOIN Courses c ON e.course_id = c.course_id
    ''').fetchall()

    return render_template('list_enrollments.html', enrollments=enrollments)

# Update enrollment (change course for a student)
@app.route('/edit_enrollment/<int:student>/<int:course>', methods=['GET', 'POST'])
def edit_enrollment(student, course):
    db = get_db()

    if request.method == 'POST':
        new_student = request.form['student_id']
        new_course = request.form['course_id']

        # Prevent duplicate enrollment (same student-course pair already exists)
        exists = db.execute('''
            SELECT 1 FROM Enrollments
            WHERE student_id = ? AND course_id = ?
        ''', (new_student, new_course)).fetchone()

        # If it exists and it's not the same record being edited, block it
        if exists and (int(new_student) != student or int(new_course) != course):
            return "❌ Oops! This student is already enrolled in this course."

        # Safe update
        db.execute('''
            UPDATE Enrollments
            SET student_id = ?, course_id = ?
            WHERE student_id = ? AND course_id = ?
        ''', (new_student, new_course, student, course))

        db.commit()
        return redirect(url_for('list_enrollments'))

    # GET request (load form data)
    students = db.execute(
        "SELECT * FROM Users WHERE role='student'"
    ).fetchall()

    courses = db.execute("SELECT * FROM Courses").fetchall()

    return render_template(
        'edit_enrollment.html',
        students=students,
        courses=courses,
        current_student=student,
        current_course=course
    )
# Delete enrollment
@app.route('/delete_enrollment/<int:student>/<int:course>')
def delete_enrollment(student, course):
    db = get_db()

    db.execute(
        'DELETE FROM Enrollments WHERE student_id = ? AND course_id = ?',
        (student, course)
    )
    db.commit()

    return redirect(url_for('list_enrollments'))

# ---------------- ASSIGNMENTS ---------------- #

# add assignment 
@app.route('/add_assignment', methods=['GET', 'POST'])
def add_assignment():
    db = get_db()

    if request.method == 'POST':
        course_id = request.form['course_id']
        title = request.form['title']
        instructions = request.form['instructions']
        due_date = request.form['due_date']

        db.execute(
            '''INSERT INTO Assignments (course_id, title, instructions, due_date)
               VALUES (?, ?, ?, ?)''',
            (course_id, title, instructions, due_date)
        )
        db.commit()

        return redirect(url_for('list_assignments'))

    courses = db.execute("SELECT * FROM Courses").fetchall()

    return render_template('add_assignment.html', courses=courses)

# list all assignments with course name, title, instructions, and due date
@app.route('/assignments')
def list_assignments():
    db = get_db()

    assignments = db.execute('''
        SELECT 
            a.assignment_id,
            a.title,
            a.instructions,
            a.due_date,
            c.course_name
        FROM Assignments a
        JOIN Courses c ON a.course_id = c.course_id
    ''').fetchall()

    return render_template('list_assignments.html', assignments=assignments)



# ---------------- SUBMISSIONS ---------------- #

# submit assignment 
@app.route('/submit', methods=['GET', 'POST'])
def submit_assignment():
    db = get_db()

    if request.method == 'POST':
        assignment_id = request.form['assignment_id']
        student_id = request.form['student_id']
        submission_date = request.form['submission_date']
        answer = request.form['answer']

        db.execute(
            '''INSERT INTO Submissions 
            (assignment_id, student_id, submission_date, answer)
            VALUES (?, ?, ?, ?)''',
            (assignment_id, student_id, submission_date, answer)
        )
        db.commit()

        return redirect(url_for('list_submissions'))

    assignments = db.execute("SELECT * FROM Assignments").fetchall()
    students = db.execute(
        "SELECT * FROM Users WHERE role='student'"
    ).fetchall()

    return render_template(
        'submit_assignment.html',
        assignments=assignments,
        students=students
    )

# list all submissions with student name, assignment title, submission date, answer, and grade
@app.route('/submissions')
def list_submissions():
    db = get_db()

    submissions = db.execute('''
        SELECT 
            u.name AS student,
            a.title,
            s.submission_date,
            s.answer,
            s.grade
        FROM Submissions s
        JOIN Users u ON s.student_id = u.user_id
        JOIN Assignments a ON s.assignment_id = a.assignment_id
    ''').fetchall()

    return render_template('list_submissions.html', submissions=submissions)

# edit assignment
@app.route('/edit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def edit_assignment(assignment_id):
    db = get_db()

    if request.method == 'POST':
        title = request.form['title']
        instructions = request.form['instructions']
        due_date = request.form['due_date']

        db.execute('''
            UPDATE Assignments
            SET title = ?, instructions = ?, due_date = ?
            WHERE assignment_id = ?
        ''', (title, instructions, due_date, assignment_id))

        db.commit()
        return redirect(url_for('list_assignments'))

    assignment = db.execute('''
        SELECT * FROM Assignments WHERE assignment_id = ?
    ''', (assignment_id,)).fetchone()

    return render_template('edit_assignment.html', assignment=assignment)

# delete assignment
@app.route('/delete_assignment/<int:assignment_id>')
def delete_assignment(assignment_id):
    db = get_db()

    db.execute('DELETE FROM Assignments WHERE assignment_id = ?', (assignment_id,))
    db.commit()

    return redirect(url_for('list_assignments'))

# grade assignments instructor login page
@app.route('/instructor_login', methods=['GET', 'POST'])
def instructor_login():
    if request.method == 'POST':
        password = request.form['password']

        if password == "instructor123":
            session['instructor'] = True
            return redirect(url_for('grade_assignments'))
        else:
            return "❌ Wrong password"

    return render_template('instructor_login.html')

# grade assignments (instructor only)
@app.route('/grade', methods=['GET', 'POST'])
def grade_assignments():

    if not session.get('instructor'):
        return redirect(url_for('instructor_login'))

    db = get_db()

    # handle grading form submission
    if request.method == 'POST':
        submission_id = request.form['submission_id']
        grade = request.form['grade']

        db.execute('''
            UPDATE Submissions
            SET grade = ?
            WHERE submission_id = ?
        ''', (grade, submission_id))

        db.commit()
        return redirect(url_for('grade_assignments'))

    # load submissions
    submissions = db.execute('''
        SELECT 
            s.submission_id,
            u.name AS student,
            a.title,
            s.answer,
            s.submission_date,
            s.grade
        FROM Submissions s
        JOIN Users u ON s.student_id = u.user_id
        JOIN Assignments a ON s.assignment_id = a.assignment_id
    ''').fetchall()

    return render_template('grade.html', submissions=submissions)

# logout instructor
@app.route('/logout')
def logout():
    session.pop('instructor', None)
    return redirect(url_for('index'))

# search functionality for users (by name, email, or role)
@app.route('/search_users', methods=['GET', 'POST'])
def search_users():
    db = get_db()
    results = []

    if request.method == 'POST':
        keyword = request.form['keyword']

        results = db.execute('''
            SELECT * FROM Users
            WHERE name LIKE ? OR email LIKE ? OR role LIKE ?
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')).fetchall()

    return render_template('search_users.html', results=results)

# search functionality for courses (by course name or instructor name)
@app.route('/search_courses', methods=['GET', 'POST'])
def search_courses():
    db = get_db()
    results = []

    if request.method == 'POST':
        keyword = request.form['keyword']

        results = db.execute('''
            SELECT c.course_id, c.course_name, u.name AS instructor
            FROM Courses c
            JOIN Users u ON c.instructor_id = u.user_id
            WHERE c.course_name LIKE ?
        ''', (f'%{keyword}%',)).fetchall()

    return render_template('search_courses.html', results=results)

# reports page showing all students enrolled in each course and number of students per course
@app.route('/reports')
def reports():
    db = get_db()

    # JOIN QUERY: students + courses
    student_courses = db.execute('''
        SELECT 
            u.name AS student_name,
            c.course_name
        FROM Enrollments e
        JOIN Users u ON e.student_id = u.user_id
        JOIN Courses c ON e.course_id = c.course_id
    ''').fetchall()

    # AGGREGATE QUERY: number of students per course
    course_counts = db.execute('''
        SELECT 
            c.course_name,
            COUNT(e.student_id) AS total_students
        FROM Courses c
        LEFT JOIN Enrollments e ON c.course_id = e.course_id
        GROUP BY c.course_id, c.course_name
    ''').fetchall()

    return render_template(
        'reports.html',
        student_courses=student_courses,
        course_counts=course_counts
    )

# initialize database on first run
with app.app_context():
    try:
        init_db()
        print("\n==============================")
        print("✅ DATABASE INITIALIZED SUCCESSFULLY")
        print("📦 Tables created: Users, Courses, Enrollments, Assignments, Submissions")
        print("==============================\n")

    except Exception as e:
        print("\n==============================")
        print("DATABASE INITIALIZATION FAILED")
        print("Error:", e)
        print("==============================\n")

# ---------------- RUN ---------------- #

if __name__ == '__main__':
    app.run(debug=True)