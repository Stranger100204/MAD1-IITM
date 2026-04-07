from flask import Blueprint, render_template, request, redirect, url_for, session
from .models import *
from .database import db

app = Blueprint("app", __name__)

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
        company = Company.query.filter_by(user_id=user.id).first()
        if company.status != "approved":
            return "Company not approved by admin"
        return redirect("/company/dashboard")
    else:
        return redirect("/student/dashboard")


# ---------------- REGISTER STUDENT ----------------
@app.route("/register/student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":

        # Create user
        user = User(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
            role="student")
        
        db.session.add(user)
        db.session.commit()

        # Create student profile
        profile = StudentProfile(
            user_id=user.id,
            roll_no=request.form.get("roll_no"),
            branch=request.form.get("branch"),
            cgpa=request.form.get("cgpa"))
        
        db.session.add(profile)
        db.session.commit()

        return redirect("/")

    return render_template("register_student.html")


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
            website=request.form.get("website"),
            status="approved"
        )
        db.session.add(company)
        db.session.commit()

        return redirect("/")   # ✅ FIX

    return render_template("register_company.html")


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
    return render_template("company_dash.html", drives=drives)


# ---------------- CREATE DRIVE ----------------
@app.route("/drive/create", methods=["GET", "POST"])
def create_drive():
    user_id = session.get("user_id")

    company = Company.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        drive = PlacementDrive(
            company_id=company.id,
            job_title=request.form.get("job_title"),
            description=request.form.get("description"),
            eligibility=request.form.get("eligibility"),
            deadline=request.form.get("deadline"),
            status="pending"   # 🔥 important (admin will approve later)
        )

        db.session.add(drive)
        db.session.commit()

        return redirect("/company/dashboard")

    return render_template("create_drive.html")

#UPDATE DRIVE
@app.route("/drive/update/<int:drive_id>", methods=["GET", "POST"])
def update_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)

    if request.method == "POST":
        drive.job_title = request.form.get("job_title")
        drive.description = request.form.get("description")
        drive.eligibility = request.form.get("eligibility")
        drive.deadline = request.form.get("deadline")

        db.session.commit()
        return redirect("/company/dashboard")

    return render_template("update_drive.html", drive=drive)

#DELETE DRIVE
@app.route("/drive/delete/<int:drive_id>")
def delete_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)

    db.session.delete(drive)
    db.session.commit()

    return redirect("/company/dashboard")

# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student/dashboard")
def student_dashboard():
    user_id = session.get("user_id")

    drives = PlacementDrive.query.filter_by(status="approved").all()

    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    student_cgpa = profile.cgpa if profile else 0

    apps = Application.query.filter_by(student_id=user_id).all()
    applied_drive_ids = [app.drive_id for app in apps]

    return render_template(
        "student_dash.html",
        drives=drives,
        applied_drive_ids=applied_drive_ids,
        student_cgpa=student_cgpa
    )


# ---------------- APPLY ----------------
@app.route("/apply/<int:drive_id>")
def apply(drive_id):
    user_id = session.get("user_id")

    # Prevent duplicate application
    existing = Application.query.filter_by(
        student_id=user_id,
        drive_id=drive_id).first()

    if existing:
        return "Already applied"

    new_app = Application(
        student_id=user_id,
        drive_id=drive_id,
        application_date="today",
        status="applied"
    )

    db.session.add(new_app)
    db.session.commit()

    return redirect("/student/dashboard")


# ---------------- VIEW APPLICATIONS ----------------
@app.route("/my_applications")
def my_applications():
    user_id = session.get("user_id")

    apps = Application.query.filter_by(student_id=user_id).all()

    # Map drives for easy access
    drives = {d.id: d for d in PlacementDrive.query.all()}

    return render_template(
        "my_applications.html",
        apps=apps,
        drives=drives
    )

#VIEW APPLICANTS FOR A DRIVE
@app.route("/drive/<int:drive_id>/applicants")
def view_applicants(drive_id):
    apps = Application.query.filter_by(drive_id=drive_id).all()

    users = {u.id: u for u in User.query.all()}
    profiles = {p.user_id: p for p in StudentProfile.query.all()}

    return render_template(
        "applicants.html",
        apps=apps,
        users=users,
        profiles=profiles
    )

#STATUS UPDATE
@app.route("/update_status/<int:app_id>/<status>")
def update_status(app_id, status):
    app_obj = Application.query.get(app_id)

    app_obj.status = status
    db.session.commit()

    return redirect(request.referrer)

# ---------------- PROFILE ROUTE ----------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")

    if not user_id:
        return redirect("/")

    user = User.query.get(user_id)

    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        profile = StudentProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()

    if request.method == "POST":
        user.email = request.form.get("email")
        profile.contact_no = request.form.get("contact_no")

        db.session.commit()
        return redirect("/student/dashboard")

    return render_template("profile.html", user=user, profile=profile)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")