from flask import Blueprint, render_template, request, redirect, url_for, session
from .models import *
from .database import db
from datetime import datetime
import random
import os
from werkzeug.utils import secure_filename

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
        if company.status == "pending":
            return "Waiting for admin approval"
        elif company.status == "rejected":
            return "Your company registration was rejected by admin"
        elif company.status == "blacklisted":
            return "Your company is blacklisted. Contact admin for more details."
        return redirect("/company/dashboard")
    elif user.role == "student":   
        if user.status == "blocked":
            return "Your account is blocked. Contact admin for more details."
        return redirect("/student/dashboard")
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
            name=request.form.get("name"),
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

        # 🔥 Generate Registration Number
        year = datetime.now().year
        random_num = random.randint(1000, 9999)
        reg_no = f"COMP{year}{random_num}"

        company = Company(
            user_id=user.id,
            company_name=request.form.get("company_name"),
            registration_no=reg_no,
            location=request.form.get("location"),
            hr_contact=request.form.get("hr_contact"),
            website=request.form.get("website"),
            status="pending"
        )

        db.session.add(company)
        db.session.commit()

        return redirect("/")

    return render_template("register_company.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():

    total_students = User.query.filter_by(role="student").count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()

    return render_template(
        "admin_dash.html",
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications
    )

# ---------------- ADMIN COMPANIES ----------------
@app.route("/admin/companies")
def admin_companies():
    companies = Company.query.all()
    users = {u.id: u for u in User.query.all()}

    return render_template(
        "admin_companies.html",
        companies=companies,
        users=users)

# ---------------- VIEW COMPANY PROFILE (ADMIN) ----------------
@app.route("/admin/company/<int:company_id>")
def admin_view_company(company_id):

    company = Company.query.get_or_404(company_id)
    user = User.query.get(company.user_id)

    return render_template(
        "view_company.html",
        company=company,
        user=user,
        role="admin"
    )

# ---------------- APPROVE COMPANY ----------------
@app.route("/admin/company/approve/<int:company_id>")
def approve_company(company_id):
    company = Company.query.get(company_id)

    company.status = "approved"
    db.session.commit()

    return redirect("/admin/companies")

# ---------------- REJECT COMPANY ----------------
@app.route("/admin/company/reject/<int:company_id>")
def reject_company(company_id):
    company = Company.query.get(company_id)

    company.status = "rejected"
    db.session.commit()

    return redirect("/admin/companies")

#--------------------- BLACKLIST COMPANY ----------------
@app.route("/admin/company/blacklist/<int:company_id>")
def blacklist_company(company_id):
    company = Company.query.get(company_id)

    company.status = "blacklisted"
    db.session.commit()

    return redirect("/admin/companies")

# ---------------- ADMIN DRIVES ----------------
@app.route("/admin/drives")
def admin_drives():
    drives = PlacementDrive.query.all()
    companies = {c.id: c for c in Company.query.all()}

    return render_template(
        "admin_drives.html",
        drives=drives,
        companies=companies)

# ---------------- APPROVE DRIVE ----------------
@app.route("/admin/drive/approve/<int:drive_id>")
def approve_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)

    drive.status = "approved"
    db.session.commit()

    return redirect("/admin/drives")

# ---------------- REJECT DRIVE ----------------
@app.route("/admin/drive/reject/<int:drive_id>")
def reject_drive(drive_id):
    drive = PlacementDrive.query.get(drive_id)

    drive.status = "rejected"
    db.session.commit()

    return redirect("/admin/drives")

#--------------------- DELETE DRIVE ----------------
@app.route("/admin/drive/delete/<int:drive_id>")
def delete_drive_admin(drive_id):
    drive = PlacementDrive.query.get(drive_id)

    db.session.delete(drive)
    db.session.commit()

    return redirect("/admin/drives")

# ---------------- COMPANY DASHBOARD ----------------
@app.route("/company/dashboard")

def company_dashboard():
    user_id = session.get("user_id")
    company = Company.query.filter_by(user_id=user_id).first()
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    today = datetime.now().date()
    return render_template("company_dash.html", drives=drives, today=today)


# ---------------- CREATE DRIVE ----------------
@app.route("/drive/create", methods=["GET", "POST"])
def create_drive():
    user_id = session.get("user_id")

    company = Company.query.filter_by(user_id=user_id).first()

    if request.method == "POST":
        deadline_str = request.form.get("deadline")
        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()

        drive = PlacementDrive(
            company_id=company.id,
            job_title=request.form.get("job_title"),
            description=request.form.get("description"),
            eligibility=float(request.form.get("eligibility")),
            deadline=deadline_date,
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
        drive.eligibility = request.form.get("eligibility")
        deadline_str = request.form.get("deadline")
        drive.deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()

        drive.status = "pending"

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
    user = User.query.get(user_id)

    if user.status == "blocked":
        session.clear()
        return "Your account has been blocked. Contact admin!"

    drives = PlacementDrive.query.filter_by(status="approved").all()

    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    student_cgpa = profile.cgpa if profile else 0

    apps = Application.query.filter_by(student_id=user_id).all()
    applied_drive_ids = [app.drive_id for app in apps]

    companies = {c.id: c for c in Company.query.all()}

    today = datetime.now().date()

    return render_template(
        "student_dash.html",
        drives=drives,
        applied_drive_ids=applied_drive_ids,
        student_cgpa=student_cgpa,
        companies=companies,
        today=today
    )

# ---------------- APPLY ----------------
@app.route("/apply/<int:drive_id>")
def apply(drive_id):
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if user.status == "blocked":
        return "Blocked users cannot apply"
    
    # Prevent duplicate application
    existing = Application.query.filter_by(
        student_id=user_id,
        drive_id=drive_id).first()

    if existing:
        return "Already applied"

    new_app = Application(
        student_id=user_id,
        drive_id=drive_id,
        date="today",
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

    companies = {c.id: c for c in Company.query.all()}

    return render_template(
        "my_applications.html",
        apps=apps,
        drives=drives,
        companies=companies
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
from flask import url_for

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

        name = request.form.get("name")
        file = request.files.get("resume")

        if file and file.filename != "":
            filename = secure_filename(file.filename)

            filepath = os.path.join("static/resumes", filename)
            file.save(filepath)

            profile.resume = filename
            
        if name:
            profile.name = name

        profile.contact_no = request.form.get("contact_no")
        profile.skills = request.form.get("skills")
        profile.summary = request.form.get("summary")

        db.session.commit()

        return redirect(url_for("app.profile"))   # ✅ FIXED

    return render_template("profile.html", user=user, profile=profile)

# ---------------- COMPANY PROFILE ROUTE ----------------
@app.route("/company/profile", methods=["GET", "POST"])
def company_profile():
    user_id = session.get("user_id")

    company = Company.query.filter_by(user_id=user_id).first()
    user = User.query.get(user_id)

    if request.method == "POST":
        company.overview = request.form.get("overview")
        company.location = request.form.get("location")
        company.services = request.form.get("services")

        company.email = request.form.get("email")
        company.hr_contact = request.form.get("contact_no")
        company.website = request.form.get("website")

        db.session.commit()

        return redirect("/company/dashboard")

    return render_template("company_profile.html", company=company, user=user)

# ---------------- VIEW STUDENT PROFILE (FOR COMPANIES) ----------------
@app.route("/student/profile/<int:user_id>")
def view_student_profile(user_id):
    user = User.query.get(user_id)
    profile = StudentProfile.query.filter_by(user_id=user_id).first()

    return render_template(
        "view_profile.html",
        user=user,
        profile=profile)

# ---------------- VIEW COMPANY PROFILE ----------------
@app.route("/company/profile/<int:company_id>")
def view_company_profile(company_id):
    company = Company.query.get_or_404(company_id)
    user = User.query.get(company.user_id)

    return render_template(
        "view_company.html",
        company=company,
        user=user,
        role=session.get("role")
    )

# ---------------- COMPANY ACTION ROTUES (FOR ADMIN) ----------------
@app.route("/admin/company/update_status/<int:company_id>/<status>")
def update_company_status(company_id, status):

    if session.get("role") != "admin":
        return "Unauthorized"

    company = Company.query.get_or_404(company_id)

    ALLOWED = ["approved", "rejected", "blacklisted"]

    if status not in ALLOWED:
        return "Invalid status"

    company.status = status
    db.session.commit()

    return redirect("/admin/companies")

# ---------------- DRIVE ACTION ROUTES (FOR ADMIN) ----------------
@app.route("/admin/drive/update_status/<int:drive_id>/<status>")
def update_drive_status(drive_id, status):

    if session.get("role") != "admin":
        return "Unauthorized"

    drive = PlacementDrive.query.get_or_404(drive_id)

    ALLOWED = ["approved", "rejected", "suspended", "terminated"]

    if status not in ALLOWED:
        return "Invalid status"

    drive.status = status
    db.session.commit()

    return redirect("/admin/drives")

# ---------------- ADMIN STUDENTS ROUTE ----------------
@app.route("/admin/students")
def admin_students():

    if session.get("role") != "admin":
        return "Unauthorized"

    students = User.query.filter_by(role="student").all()

    profiles = {p.user_id: p for p in StudentProfile.query.all()}
    apps = Application.query.all()
    drives = {d.id: d for d in PlacementDrive.query.all()}
    companies = {c.id: c for c in Company.query.all()}

    return render_template(
        "admin_students.html",
        students=students,
        profiles=profiles,
        apps=apps,
        drives=drives,
        companies=companies
    )


# ---------------- SEARCH ROUTE ----------------
@app.route("/admin/search")
def admin_search():

    if session.get("role") != "admin":
        return "Unauthorized"

    query = request.args.get("q")
    search_type = request.args.get("type")   # 🔥 NEW

    if not query:
        return redirect("/admin/dashboard")

    # Default empty lists
    students = []
    companies = []
    drives = []

    # Mapping
    profiles = {p.user_id: p for p in StudentProfile.query.all()}
    company_map = {c.id: c for c in Company.query.all()}

    # 🔍 STUDENT SEARCH
    if search_type == "student":

        students = db.session.query(User).join(StudentProfile).filter(
            User.role == "student",
            (
                User.username.ilike(f"%{query}%") |
                StudentProfile.name.ilike(f"%{query}%")
            )
        ).all()

        # 🔥 HANDLE ID SEARCH
        clean_query = query.upper().replace("STU-", "").strip()

        if clean_query.isdigit():
            real_id = int(clean_query) + 1   # +1 because admin is ID 1

            students += User.query.filter_by(
                id=real_id,
                role="student"
            ).all()

    # 🔍 COMPANY SEARCH
    elif search_type == "company":

        companies = Company.query.filter(
            Company.company_name.contains(query)
        ).all()

        if query.isdigit():
            companies += Company.query.filter_by(id=int(query)).all()

    # 🔍 DRIVE SEARCH
    elif search_type == "drive":

        drives = PlacementDrive.query.filter(
            PlacementDrive.job_title.contains(query)
        ).all()

    # 🔥 REMOVE DUPLICATES (important)
    students = list({s.id: s for s in students}.values())
    companies = list({c.id: c for c in companies}.values())

    return render_template(
        "search_results.html",
        students=students,
        companies=companies,
        drives=drives,
        profiles=profiles,
        companies_map=company_map,   # for drive display
        type=search_type,
        query=query
    )

# ---------------- BLOCK/UNBLOCK STUDENT ----------------
@app.route("/admin/student/toggle/<int:user_id>")
def toggle_student(user_id):

    if session.get("role") != "admin":
        return "Unauthorized"

    student = User.query.get_or_404(user_id)

    if student.role != "student":
        return "Invalid"

    student.status = "blocked" if student.status == "active" else "active"

    db.session.commit()

    return redirect("/admin/students")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")