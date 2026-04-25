# EduTrack - Learning Management System

## Overview

EduTrack is a Flask-based Learning Management System (LMS) designed to manage users, courses, assignments, and submissions. The system supports role-based access for students and instructors, enabling assignment creation, submission, and grading.


## Features

* User Management (Students & Instructors)
* Course Creation and Enrollment
* Assignment Creation with Instructions
* Assignment Submission (Text-based answers)
* Instructor Grading System
* Search Functionality (Users & Courses)
* Role-Based Access Control


## Technologies Used

* Python (Flask Framework)
* SQLite Database
* HTML, CSS (Jinja2 Templates)


## Installation

1. Clone the repository:

```bash
git clone https://github.com/ReddySrujana/EduTrack.git
cd EduTrack
```

2. Install dependencies:

```bash
pip install flask
```

3. Run the application:

```bash
python app.py
```

4. Open browser:

```
http://127.0.0.1:5000/
```

## Screenshots

### 1. Home Page

![Home Page](screenshots/home.png)


### 2. Add User

![Add User](screenshots/add_user.png)


### 3. Users List

![Users List](screenshots/users.png)


### 4. Add Course

![Add Course](screenshots/add_course.png)


### 5. Courses List

![Courses List](screenshots/courses.png)


### 6. Add Assignment

![Add Assignment](screenshots/add_assignment.png)


### 7. Assignments List

![Assignments](screenshots/assignments.png)



### 8. Submit Assignment

![Submit](screenshots/submit.png)


### 9. Submissions View

![Submissions](screenshots/submissions.png)



### 10. Instructor Login

![Login](screenshots/login.png)


### 11. Grade Assignments

![Grading](screenshots/grade.png)


## Usage

* Instructors:

  * Create courses
  * Add assignments
  * Grade submissions (via login)

* Students:

  * Enroll in courses
  * Submit assignments

## Instructor Access

To access grading:

```
Password: instructor123
```


## Future Improvements

* Full authentication system (login/signup)
* File upload submissions
* Dashboard analytics
* Deployment (Heroku/AWS)
