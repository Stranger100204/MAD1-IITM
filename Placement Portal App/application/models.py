from .database import db


# ---------------- USER ----------------
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(), nullable=False)


# ---------------- COMPANY ----------------
class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))  # ✅ FIXED TYPE
    company_name = db.Column(db.String(), nullable=False)
    hr_contact = db.Column(db.String())
    website = db.Column(db.String())
    status = db.Column(db.String(), default='pending')


# ---------------- PLACEMENT DRIVE ----------------
class PlacementDrive(db.Model):
    __tablename__ = "placement_drive"   # ✅ IMPORTANT

    id = db.Column(db.Integer(), primary_key=True)
    company_id = db.Column(db.Integer(), db.ForeignKey('company.id'))
    job_title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String())
    eligibility = db.Column(db.String())
    deadline = db.Column(db.String())
    status = db.Column(db.String(), default='pending')


# ---------------- APPLICATION ----------------
class Application(db.Model):
    __tablename__ = "application"

    id = db.Column(db.Integer(), primary_key=True)
    student_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    drive_id = db.Column(db.Integer(), db.ForeignKey('placement_drive.id'), nullable=False)
    date = db.Column(db.String(), nullable=False)
    status = db.Column(db.String(), nullable=False, default='applied')


class StudentProfile(db.Model):
    __tablename__ = "student_profile"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))

    cgpa = db.Column(db.Float())
    roll_no = db.Column(db.String())
    contact_no = db.Column(db.String())
    branch = db.Column(db.String())