from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)

# ---------- MODELS ----------

class Course(db.Model):
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String, nullable=False)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_description = db.Column(db.String)

class Student(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)

class Enrollment(db.Model):
    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.student_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)


# ---------- STUDENT ----------

class StudentList(Resource):
    def post(self):
        data = request.get_json()

        if not data.get("roll_number"):
            return {"error_code": "STUDENT001", "message": "Roll Number required"}, 400
        if not data.get("first_name"):
            return {"error_code": "STUDENT002", "message": "First Name is required"}, 400

        if Student.query.filter_by(roll_number=data["roll_number"]).first():
            return {"message": "Duplicate"}, 409

        s = Student(
            roll_number=data["roll_number"],
            first_name=data["first_name"],
            last_name=data.get("last_name")
        )
        db.session.add(s)
        db.session.commit()

        return {"student_id": s.student_id}, 201


class StudentResource(Resource):
    def get(self, student_id):
        s = Student.query.get(student_id)
        if not s:
            return {"message": "Not found"}, 404

        return {
            "student_id": s.student_id,
            "roll_number": s.roll_number,
            "first_name": s.first_name,
            "last_name": s.last_name
        }, 200

    def put(self, student_id):
        s = Student.query.get(student_id)
        if not s:
            return {"message": "Not found"}, 404

        data = request.get_json()
        s.roll_number = data.get("roll_number", s.roll_number)
        s.first_name = data.get("first_name", s.first_name)
        s.last_name = data.get("last_name", s.last_name)

        db.session.commit()
        return {}, 200

    def delete(self, student_id):
        s = Student.query.get(student_id)
        if not s:
            return {"message": "Not found"}, 404

        db.session.delete(s)
        db.session.commit()
        return {}, 200


# ---------- COURSE ----------

class CourseList(Resource):
    def post(self):
        data = request.get_json()

        if not data.get("course_name"):
            return {"error_code": "COURSE001", "message": "Course Name is required"}, 400
        if not data.get("course_code"):
            return {"error_code": "COURSE002", "message": "Course Code is required"}, 400

        if Course.query.filter_by(course_code=data["course_code"]).first():
            return {"message": "Duplicate"}, 409

        c = Course(
            course_name=data["course_name"],
            course_code=data["course_code"],
            course_description=data.get("course_description")
        )
        db.session.add(c)
        db.session.commit()

        return {"course_id": c.course_id}, 201


class CourseResource(Resource):
    def get(self, course_id):
        c = Course.query.get(course_id)
        if not c:
            return {"message": "Not found"}, 404

        return {
            "course_id": c.course_id,
            "course_name": c.course_name,
            "course_code": c.course_code,
            "course_description": c.course_description
        }, 200

    def put(self, course_id):
        c = Course.query.get(course_id)
        if not c:
            return {"message": "Not found"}, 404

        data = request.get_json()
        c.course_name = data.get("course_name", c.course_name)
        c.course_code = data.get("course_code", c.course_code)
        c.course_description = data.get("course_description", c.course_description)

        db.session.commit()
        return {}, 200

    def delete(self, course_id):
        c = Course.query.get(course_id)
        if not c:
            return {"message": "Not found"}, 404

        db.session.delete(c)
        db.session.commit()
        return {}, 200


# ---------- ENROLLMENT ----------

class EnrollmentAPI(Resource):
    def post(self, student_id):
        data = request.get_json()
        course_id = data.get("course_id")

        student = Student.query.get(student_id)
        course = Course.query.get(course_id)

        if not course:
            return {"error_code": "ENROLLMENT001", "message": "Course does not exist"}, 400
        if not student:
            return {"error_code": "ENROLLMENT002", "message": "Student does not exist"}, 400

        e = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(e)
        db.session.commit()

        return {
            "enrollment_id": e.enrollment_id,
            "student_id": student_id,
            "course_id": course_id
        }, 201

    def get(self, student_id):
        student = Student.query.get(student_id)
        if not student:
            return {"message": "Not found"}, 404

        enrolls = Enrollment.query.filter_by(student_id=student_id).all()

        if not enrolls:
            return {"message": "Not found"}, 404

        result = []
        for e in enrolls:
            result.append({
                "enrollment_id": e.enrollment_id,
                "student_id": e.student_id,
                "course_id": e.course_id
            })

        return result, 200


class EnrollmentDelete(Resource):
    def delete(self, student_id, course_id):
        e = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id
        ).first()

        if not e:
            return {"message": "Not found"}, 404

        db.session.delete(e)
        db.session.commit()
        return {}, 200


# ---------- ROUTES ----------

api.add_resource(StudentList, "/api/student")
api.add_resource(StudentResource, "/api/student/<int:student_id>")

api.add_resource(CourseList, "/api/course")
api.add_resource(CourseResource, "/api/course/<int:course_id>")

api.add_resource(EnrollmentAPI, "/api/student/<int:student_id>/course")
api.add_resource(EnrollmentDelete, "/api/student/<int:student_id>/course/<int:course_id>")


if __name__ == "__main__":
    app.run(debug=True)