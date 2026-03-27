from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODELS ------------------

class Student(db.Model):
    __tablename__ = 'student'

    student_id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)


class Course(db.Model):
    __tablename__ = 'course'

    course_id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)


class Enrollment(db.Model):
    __tablename__ = 'enrollment'

    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)


# ------------------ STUDENT API ------------------

class StudentAPI(Resource):

    def get(self, student_id):
        student = Student.query.get(student_id)
        if not student:
            return {"error_code": "STUDENT001", "message": "Student not found"}, 404

        return {
            "student_id": student.student_id,
            "roll_number": student.roll_number,
            "first_name": student.first_name,
            "last_name": student.last_name
        }

    def put(self, student_id):
        student = Student.query.get(student_id)
        if not student:
            return {"error_code": "STUDENT001", "message": "Student not found"}, 404

        data = request.get_json()

        # revert to safe update (original correct behavior)
        if 'first_name' in data:
            student.first_name = data['first_name']

        if 'last_name' in data:
            student.last_name = data['last_name']

        db.session.commit()

        return {"message": "Student updated"}

    def delete(self, student_id):
        student = Student.query.get(student_id)
        if not student:
            return {"error_code": "STUDENT001", "message": "Student not found"}, 404

        Enrollment.query.filter_by(student_id=student_id).delete()

        db.session.delete(student)
        db.session.commit()

        return {"message": "Deleted"}


class StudentListAPI(Resource):

    def post(self):
        data = request.get_json()

        if not data.get('roll_number'):
            return {"error_code": "STUDENT001", "message": "Roll Number required"}, 400

        if not data.get('first_name'):
            return {"error_code": "STUDENT002", "message": "First Name required"}, 400

        existing = Student.query.filter_by(roll_number=data['roll_number']).first()
        if existing:
            return {"error_code": "STUDENT003", "message": "Roll number already exists"}, 409

        student = Student(
            roll_number=data['roll_number'],
            first_name=data['first_name'],
            last_name=data.get('last_name')
        )

        db.session.add(student)
        db.session.commit()

        return {"message": "Student created"}, 201


# ------------------ COURSE API ------------------

class CourseAPI(Resource):

    def get(self, course_id):
        course = Course.query.get(course_id)

        if not course:
            return {"error_code": "COURSE001", "message": "Course not found"}, 404

        return {
            "course_id": course.course_id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "course_description": course.course_description
        }

    def put(self, course_id):
        course = Course.query.get(course_id)

        if not course:
            return {"error_code": "COURSE001", "message": "Course not found"}, 404

        data = request.get_json()

        if not data.get('course_name'):
            return {"error_code": "COURSE001", "message": "Course Name is required"}, 400

        if not data.get('course_code'):
            return {"error_code": "COURSE002", "message": "Course Code is required"}, 400

        course.course_name = data['course_name']
        course.course_code = data['course_code']
        course.course_description = data.get('course_description')

        db.session.commit()

        return {"message": "Course updated"}

    def delete(self, course_id):
        course = Course.query.get(course_id)

        if not course:
            return {"error_code": "COURSE001", "message": "Course not found"}, 404

        db.session.delete(course)
        db.session.commit()

        return {"message": "Course deleted"}


class CourseListAPI(Resource):

    def post(self):
        data = request.get_json()

        if not data.get('course_name'):
            return {"error_code": "COURSE001", "message": "Course Name is required"}, 400

        if not data.get('course_code'):
            return {"error_code": "COURSE002", "message": "Course Code is required"}, 400

        existing = Course.query.filter_by(course_code=data['course_code']).first()
        if existing:
            return {"error_code": "COURSE003", "message": "Course already exists"}, 409

        course = Course(
            course_name=data['course_name'],
            course_code=data['course_code'],
            course_description=data.get('course_description')
        )

        db.session.add(course)
        db.session.commit()

        return {"message": "Course created"}, 201


# ------------------ ENROLLMENT API ------------------

class StudentCourseAPI(Resource):

    def get(self, student_id):
        student = Student.query.get(student_id)

        if not student:
            return {"error_code": "ENROLLMENT002", "message": "Student does not exist."}, 404

        enrollments = Enrollment.query.filter_by(student_id=student_id).all()

        result = []
        for e in enrollments:
            result.append({
                "enrollment_id": e.enrollment_id,
                "student_id": e.student_id,
                "course_id": e.course_id
            })

        return result

    def post(self, student_id):
        student = Student.query.get(student_id)

        if not student:
            return {"error_code": "ENROLLMENT002", "message": "Student does not exist."}, 404

        data = request.get_json()
        course_id = data.get('course_id')

        course = Course.query.get(course_id)
        if not course:
            return {"error_code": "ENROLLMENT001", "message": "Course does not exist"}, 404

        existing = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id
        ).first()

        if existing:
            return {"message": "Already enrolled"}, 400

        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id
        )

        db.session.add(enrollment)
        db.session.commit()

        return {
            "enrollment_id": enrollment.enrollment_id,
            "student_id": student_id,
            "course_id": course_id
        }, 201


class StudentCourseDeleteAPI(Resource):

    def delete(self, student_id, course_id):

        student = Student.query.get(student_id)
        if not student:
            return {"error_code": "ENROLLMENT002", "message": "Student does not exist."}, 404

        course = Course.query.get(course_id)
        if not course:
            return {"error_code": "ENROLLMENT001", "message": "Course does not exist"}, 404

        enrollment = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id
        ).first()

        if not enrollment:
            return {"error_code": "ENROLLMENT003", "message": "Enrollment does not exist"}, 404

        db.session.delete(enrollment)
        db.session.commit()

        return {"message": "Enrollment deleted"}
    
# ------------------ ROUTES ------------------

api.add_resource(StudentAPI, '/api/student/<int:student_id>')
api.add_resource(StudentListAPI, '/api/student')

api.add_resource(CourseAPI, '/api/course/<int:course_id>')
api.add_resource(CourseListAPI, '/api/course')

api.add_resource(StudentCourseAPI, '/api/student/<int:student_id>/course')
api.add_resource(StudentCourseDeleteAPI, '/api/student/<int:student_id>/course/<int:course_id>')