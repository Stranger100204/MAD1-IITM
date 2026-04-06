from .database import db #Uses current folder to import database.py and get db variable from it

class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(), nullable=False)

class Company(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey('user.id'))
    company_name = db.Column(db.String(), nullable=False)
    hr_contact = db.Column(db.String())
    website = db.Column(db.String())
    status = db.Column(db.String(), default='pending')

class Application(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    student_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    drive_id = db.Column(db.Integer(), db.ForeignKey('placement_drive.id'), nullable=False)
    date = db.Column(db.String(), nullable=False)
    time_slot = db.Column(db.String(), nullable=False)
    status = db.Column(db.String(), nullable=False, default='applied')