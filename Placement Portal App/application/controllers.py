from flask import render_template, request, redirect, url_for, session
from flask import current_app as app
from .models import *
from .database import db


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("login.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("pwd")

    user = User.query.filter_by(username=username, password=password).first()

    if not user:
        return "Invalid Credentials"

    session["user_id"] = user.id
    session["role"] = user.role

    if user.role == "admin":
        return redirect("/admin/dashboard")
    elif user.role == "company":
        return redirect("/company/dashboard")
    else:
        return redirect("/student/dashboard")


# ---------------- REGISTER STUDENT ----------------
@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
            role="student"
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/")
    return render_template("register.html")


# ---------------- REGISTER COMPANY ----------------
@app.route("/register/company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
            role="company"
        )
        db.session.add(user)
        db.session.commit()

        company = Company(
            user_id=user.id,
            company_name=request.form.get("company_name"),
            hr_contact=request.form.get("hr_contact"),
            website=request.form.get("website")
        )
        db.session.add(company)
        db.session.commit()

        return "Registered. Wait for admin approval."

    return render_template("register.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    companies = Company.query.all()
    drives = PlacementDrive.query.all()
    students = User.query.filter_by(role="student").all()
    return render_template("manager_dash.html", companies=companies, drives=drives, students=students)


# ---------------- APPROVE COMPANY ----------------
@app.route("/approve/company/<int:id>")
def approve_company(id):
    company = Company.query.get(id)
    company.status = "approved"
    db.session.commit()
    return redirect("/admin/dashboard")


# ---------------- APPROVE DRIVE ----------------
@app.route("/approve/drive/<int:id>")
def approve_drive(id):
    drive = PlacementDrive.query.get(id)
    drive.status = "approved"
    db.session.commit()
    return redirect("/admin/dashboard")


# ---------------- COMPANY DASHBOARD ----------------
@app.route("/company/dashboard")
def company_dashboard():
    user_id = session.get("user_id")
    company = Company.query.filter_by(user_id=user_id).first()
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    return render_template("manager_dash.html", drives=drives)


# ---------------- CREATE DRIVE ----------------
@app.route("/drive/create", methods=["GET", "POST"])
def create_drive():
    if request.method == "POST":
        user_id = session.get("user_id")
        company = Company.query.filter_by(user_id=user_id).first()

        if company.status != "approved":
            return "Company not approved by admin"

        drive = PlacementDrive(
            company_id=company.id,
            job_title=request.form.get("job_title"),
            description=request.form.get("description"),
            eligibility=request.form.get("eligibility"),
            deadline=request.form.get("deadline")
        )
        db.session.add(drive)
        db.session.commit()
        return redirect("/company/dashboard")

    return render_template("create_table.html")


# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student/dashboard")
def student_dashboard():
    drives = PlacementDrive.query.filter_by(status="approved").all()
    return render_template("user_dash.html", drives=drives)


# ---------------- APPLY ----------------
@app.route("/apply/<int:drive_id>")
def apply(drive_id):
    user_id = session.get("user_id")

    existing = Application.query.filter_by(student_id=user_id, drive_id=drive_id).first()
    if existing:
        return "Already applied"

    app_obj = Application(
        student_id=user_id,
        drive_id=drive_id,
        date="today"
    )
    db.session.add(app_obj)
    db.session.commit()

    return redirect("/student/dashboard")


# ---------------- VIEW APPLICATIONS ----------------
@app.route("/my_applications")
def my_applications():
    user_id = session.get("user_id")
    apps = Application.query.filter_by(student_id=user_id).all()
    return render_template("user_req.html", apps=apps)