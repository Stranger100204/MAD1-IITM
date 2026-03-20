from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODELS ------------------

class Student(db.Model):
    __tablename__ = 'student'

    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)

class Course(db.Model):
    __tablename__ = 'course'

    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)

class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    estudent_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    ecourse_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)

    student = db.relationship('Student', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

# ------------------ ROUTES ------------------

@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)

@app.route('/student/create', methods=['GET', 'POST'])
def create_student():

    if request.method == 'GET':
        return render_template('create.html')

    if request.method == 'POST':

        roll = request.form.get('roll')
        f_name = request.form.get('f_name')
        l_name = request.form.get('l_name')

        # Check duplicate roll number
        existing = Student.query.filter_by(roll_number=roll).first()
        if existing:
            return render_template('error.html')

        # Create student
        new_student = Student(
            roll_number=roll,
            first_name=f_name,
            last_name=l_name
        )

        db.session.add(new_student)
        db.session.commit()   # commit to get student_id

        # Handle courses
        selected_courses = request.form.getlist('courses')

        for course in selected_courses:
            course_id = int(course.split('_')[1])  # course_1 → 1

            enrollment = Enrollment(
                estudent_id=new_student.student_id,
                ecourse_id=course_id
            )

            db.session.add(enrollment)

        db.session.commit()

        return redirect('/')

@app.route('/student/<int:student_id>/update', methods=['GET', 'POST'])
def update_student(student_id):

    student = Student.query.get(student_id)

    if request.method == 'GET':
        return render_template('update.html', student=student)

    if request.method == 'POST':

        # Update basic details
        student.first_name = request.form.get('f_name')
        student.last_name = request.form.get('l_name')

        # DELETE old enrollments
        Enrollment.query.filter_by(estudent_id=student_id).delete()

        # ADD new enrollments
        selected_courses = request.form.getlist('courses')

        for course in selected_courses:
            course_id = int(course.split('_')[1])

            new_enroll = Enrollment(
                estudent_id=student_id,
                ecourse_id=course_id
            )
            db.session.add(new_enroll)

        db.session.commit()

        return redirect('/')
    
@app.route('/student/<int:student_id>')
def student_details(student_id):

    student = Student.query.get(student_id)

    enrollments = Enrollment.query.filter_by(estudent_id=student_id).all()

    return render_template(
        'details.html',
        student=student,
        enrollments=enrollments
    )

@app.route('/student/<int:student_id>/delete')
def delete_student(student_id):

    # Delete enrollments first
    Enrollment.query.filter_by(estudent_id=student_id).delete()

    # Delete student
    student = Student.query.get(student_id)
    db.session.delete(student)

    db.session.commit()

    return redirect('/')

# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(debug=True)