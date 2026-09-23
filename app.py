from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    Response,
    send_from_directory
)

from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader

from utils.ai_match import analyze_resume

# =========================================================
# EMAIL NOTIFICATION
# =========================================================

from email_sender import send_candidate_email


# =========================================================
# DATABASE
# =========================================================

from database import (
    create_database,
    save_candidate,
    get_all_candidates,
    search_candidates,
    delete_candidate,
    get_candidate_by_id,
    update_candidate,
    get_ranked_candidates,
    get_total_count,
    get_status_count,
    get_previous_applications,
    get_previous_application_count,
    add_application_date_column,
    get_user_by_email,
    create_user,
    get_user_applications,
    reset_user_password
)

import os
import csv
import io


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = "resume_screening_secret_key"


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# =========================================================
# UPLOAD FOLDER
# =========================================================

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# ALLOWED FILE EXTENSIONS
# =========================================================

ALLOWED_EXTENSIONS = {
    "pdf"
}


# =========================================================
# CREATE UPLOAD FOLDER
# =========================================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# ADMIN LOGIN
# =========================================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

create_database()

add_application_date_column()


# =========================================================
# FILE EXTENSION CHECK
# =========================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# LOGIN REQUIRED HELPER
# =========================================================

def is_admin_logged_in():

    return session.get(
        "admin_logged_in",
        False
    )


# =========================================================
# WELCOME PAGE
# =========================================================

@app.route("/")
def welcome():

    return render_template(
        "welcome.html"
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session[
                "admin_logged_in"
            ] = True

            return redirect(
                url_for("home")
            )

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGIN COMPATIBILITY
# =========================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    username = request.form.get(
        "username",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if (
        username == ADMIN_USERNAME
        and
        password == ADMIN_PASSWORD
    ):

        session[
            "admin_logged_in"
        ] = True

        return redirect(
            url_for("home")
        )

    return render_template(
        "login.html",
        error="Invalid username or password"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("admin")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/home")
def home():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    return render_template(
        "index.html"
    )


# =========================================================
# HOME PAGE COMPATIBILITY
# =========================================================

app.add_url_rule(
    "/home",
    endpoint="home_page",
    view_func=home
)


# =========================================================
# INDEX COMPATIBILITY
# =========================================================

app.add_url_rule(
    "/index",
    endpoint="index",
    view_func=home
)


# =========================================================
# RESUME ANALYSIS PAGE
# =========================================================

@app.route("/resume-analysis")
def resume_analysis():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    return render_template(
        "resume_analysis.html"
    )


# =========================================================
# AI MATCHING PAGE
# =========================================================

@app.route("/ai-matching")
def ai_matching():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    return render_template(
        "ai_matching.html"
    )


# =========================================================
# UPLOAD RESUME
# =========================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )


    # -----------------------------------------------------
    # FORM DATA
    # -----------------------------------------------------

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    job_description = request.form.get(
        "job_description",
        ""
    ).strip()

    file = request.files.get(
        "resume"
    )


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not name:

        return "Candidate name is required"

    if not email:

        return "Candidate email is required"

    if not file:

        return "Please select a PDF resume"

    if file.filename == "":

        return "Please select a PDF resume"

    if not allowed_file(
        file.filename
    ):

        return "Only PDF files are allowed"


    # -----------------------------------------------------
    # SAVE RESUME
    # -----------------------------------------------------

    filename = secure_filename(
        file.filename
    )

    if not filename:

        return "Invalid resume filename"

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    try:

        file.save(
            file_path
        )

    except Exception as e:

        return (
            "Error saving resume: "
            + str(e)
        )


    # -----------------------------------------------------
    # EXTRACT PDF TEXT
    # -----------------------------------------------------

    resume_text = ""

    try:

        reader = PdfReader(
            file_path
        )

        for page in reader.pages:

            text = page.extract_text()

            if text:

                resume_text += (
                    text + "\n"
                )

    except Exception as e:

        return (
            "Error reading PDF: "
            + str(e)
        )


    # -----------------------------------------------------
    # AI ANALYSIS
    # -----------------------------------------------------

    try:

        result = analyze_resume(
            resume_text,
            job_description
        )

    except Exception as e:

        return (
            "Error during AI analysis: "
            + str(e)
        )


    # -----------------------------------------------------
    # AI RESULTS
    # -----------------------------------------------------

    score = result.get(
        "score",
        0
    )

    matched_skills = result.get(
        "matched_skills",
        []
    )

    missing_skills = result.get(
        "missing_skills",
        []
    )

    tfidf_score = result.get(
        "tfidf_score",
        0
    )

    skill_score = result.get(
        "skill_score",
        0
    )

    job_skills = result.get(
        "job_skills",
        []
    )


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if score >= 50:

        status = "Selected"

    else:

        status = "Rejected"


    # -----------------------------------------------------
    # SAVE APPLICATION
    # -----------------------------------------------------

    try:

        save_candidate(
            name,
            email,
            phone,
            filename,
            score,
            status,
            tfidf_score,
            skill_score,
            matched_skills,
            missing_skills
        )

    except Exception as e:

        return (
            "Database save error: "
            + str(e)
        )


    # =====================================================
    # EMAIL NOTIFICATION
    # =====================================================

    try:

        email_sent = send_candidate_email(
            email,
            name,
            score,
            status
        )

        if email_sent:

            print(
                "Candidate email notification sent successfully."
            )

        else:

            print(
                "Candidate email notification was not sent."
            )

    except Exception as e:

        print(
            "Email notification error: "
            + str(e)
        )


    # -----------------------------------------------------
    # RESULT PAGE
    # -----------------------------------------------------

    return render_template(
        "result.html",

        name=name,

        email=email,

        phone=phone,

        score=score,

        status=status,

        matched_skills=matched_skills,

        missing_skills=missing_skills,

        tfidf_score=tfidf_score,

        skill_score=skill_score,

        job_skills=job_skills,

        filename=filename
    )


# =========================================================
# CANDIDATE REGISTER
# =========================================================

@app.route("/candidate/register", methods=["GET", "POST"])
def candidate_register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            return render_template("candidate_register.html", error="All fields are required.")

        if password != confirm_password:
            return render_template("candidate_register.html", error="Passwords do not match.")

        if len(password) < 6:
            return render_template("candidate_register.html", error="Password must contain at least 6 characters.")

        if get_user_by_email(email):
            return render_template("candidate_register.html", error="An account with this email already exists.")

        try:
            create_user(name, email, password)
        except Exception as e:
            return render_template("candidate_register.html", error="Registration failed: " + str(e))

        return redirect(url_for("candidate_login", registered="1"))

    return render_template("candidate_register.html")


# =========================================================
# CANDIDATE LOGIN
# =========================================================

@app.route("/candidate/login", methods=["GET", "POST"])
def candidate_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)

        if not user:
            return render_template("candidate_login.html", error="Invalid email or password.")

        from werkzeug.security import check_password_hash

        if not check_password_hash(user[3], password):
            return render_template("candidate_login.html", error="Invalid email or password.")

        session.clear()
        session["candidate_logged_in"] = True
        session["candidate_email"] = email
        session["candidate_name"] = user[1]

        return redirect(url_for("candidate_dashboard"))

    registered = request.args.get("registered")
    return render_template("candidate_login.html", registered=registered)


# =========================================================
# CANDIDATE FORGOT PASSWORD
# =========================================================

@app.route("/candidate/forgot-password", methods=["GET", "POST"])
def candidate_forgot_password():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not new_password or not confirm_password:
            return render_template(
                "candidate_forgot_password.html",
                error="All fields are required."
            )

        if new_password != confirm_password:
            return render_template(
                "candidate_forgot_password.html",
                error="Passwords do not match."
            )

        if len(new_password) < 6:
            return render_template(
                "candidate_forgot_password.html",
                error="Password must contain at least 6 characters."
            )

        if not get_user_by_email(email):
            return render_template(
                "candidate_forgot_password.html",
                error="No candidate account found with this email."
            )

        try:
            reset_user_password(email, new_password)
        except Exception as e:
            return render_template(
                "candidate_forgot_password.html",
                error="Password reset failed: " + str(e)
            )

        return redirect(url_for("candidate_login", reset="1"))

    return render_template("candidate_forgot_password.html")


# =========================================================
# CANDIDATE DASHBOARD
# =========================================================

@app.route("/candidate/dashboard")
def candidate_dashboard():

    if not session.get("candidate_logged_in"):
        return redirect(url_for("candidate_login"))

    email = session.get("candidate_email", "")

    applications = get_user_applications(email)

    return render_template(
        "candidate_dashboard.html",
        candidate_name=session.get("candidate_name", "Candidate"),
        email=email,
        applications=applications
    )


# =========================================================
# CANDIDATE LOGOUT
# =========================================================

@app.route("/candidate/logout")
def candidate_logout():

    session.clear()
    return redirect(url_for("candidate_login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    candidates = get_all_candidates()

    total = get_total_count()

    selected = get_status_count(
        "Selected"
    )

    rejected = get_status_count(
        "Rejected"
    )

    return render_template(
        "dashboard.html",

        candidates=candidates,

        total=total,

        selected=selected,

        rejected=rejected
    )


# =========================================================
# DASHBOARD SEARCH
# =========================================================

@app.route(
    "/dashboard/search",
    methods=["GET"]
)
def dashboard_search():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    keyword = request.args.get(
        "q",
        ""
    ).strip()

    if keyword:

        candidates = search_candidates(
            keyword
        )

    else:

        candidates = get_all_candidates()

    total = get_total_count()

    selected = get_status_count(
        "Selected"
    )

    rejected = get_status_count(
        "Rejected"
    )

    return render_template(
        "dashboard.html",

        candidates=candidates,

        total=total,

        selected=selected,

        rejected=rejected,

        search_query=keyword
    )


# =========================================================
# SELECTED CANDIDATES
# =========================================================

@app.route("/selected")
def selected_candidates():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    candidates = get_all_candidates()

    selected = [
        candidate
        for candidate in candidates
        if len(candidate) > 6
        and candidate[6] == "Selected"
    ]


    # -----------------------------------------------------
    # PREVIOUS APPLICATION COUNT
    # -----------------------------------------------------

    previous_counts = {}

    for candidate in selected:

        candidate_id = candidate[0]

        email = candidate[2]

        previous_counts[
            candidate_id
        ] = get_previous_application_count(
            email
        )


    return render_template(
        "selected.html",

        candidates=selected,

        previous_counts=previous_counts
    )


# =========================================================
# SELECTED ENDPOINT COMPATIBILITY
# FIX FOR:
# BuildError: Could not build url for endpoint 'selected'
# =========================================================

app.add_url_rule(
    "/selected",
    endpoint="selected",
    view_func=selected_candidates
)


# =========================================================
# REJECTED CANDIDATES
# =========================================================

@app.route("/rejected")
def rejected_candidates():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    candidates = get_all_candidates()

    rejected = [
        candidate
        for candidate in candidates
        if len(candidate) > 6
        and candidate[6] == "Rejected"
    ]

    return render_template(
        "rejected.html",

        candidates=rejected
    )


# =========================================================
# REJECTED ENDPOINT COMPATIBILITY
# =========================================================

app.add_url_rule(
    "/rejected",
    endpoint="rejected",
    view_func=rejected_candidates
)


# =========================================================
# APPLICATION HISTORY - ALL
# =========================================================
# This fixes:
# http://127.0.0.1:5000/application-history
# 404 Page Not Found
# =========================================================

@app.route(
    "/application-history"
)
def application_history_all():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )


    # -----------------------------------------------------
    # GET ALL CANDIDATES
    # -----------------------------------------------------

    candidates = get_all_candidates()


    # -----------------------------------------------------
    # COLLECT ALL APPLICATION HISTORY
    # -----------------------------------------------------

    all_applications = []

    processed_emails = set()


    for candidate in candidates:

        if len(candidate) <= 2:

            continue

        email = candidate[2]

        if not email:

            continue

        if email in processed_emails:

            continue

        processed_emails.add(
            email
        )

        try:

            applications = get_previous_applications(
                email
            )

            if applications:

                all_applications.extend(
                    applications
                )

        except Exception as e:

            print(
                "History error for "
                + email
                + ": "
                + str(e)
            )


    # -----------------------------------------------------
    # SORT BY APPLICATION DATE
    # -----------------------------------------------------

    try:

        all_applications.sort(
            key=lambda x: (
                x[7]
                if len(x) > 7 and x[7]
                else ""
            ),
            reverse=True
        )

    except Exception:

        pass


    return render_template(
        "history.html",

        applications=all_applications,

        email="All Applications"
    )


# =========================================================
# APPLICATION HISTORY - SPECIFIC EMAIL
# =========================================================

@app.route(
    "/application-history/<path:email>"
)
def application_history(email):

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    applications = get_previous_applications(
        email
    )

    return render_template(
        "history.html",

        applications=applications,

        email=email
    )


# =========================================================
# APPLICATION HISTORY ENDPOINT COMPATIBILITY
# =========================================================

app.add_url_rule(
    "/application-history",
    endpoint="history",
    view_func=application_history_all
)


# =========================================================
# APPLICATION DETAILS
# =========================================================

@app.route(
    "/application-details/<int:candidate_id>"
)
def application_details(candidate_id):

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    candidate = get_candidate_by_id(
        candidate_id
    )

    if not candidate:

        return "Application not found", 404

    return render_template(
        "application_details.html",

        candidate=candidate
    )


# =========================================================
# APPLICATION DETAILS COMPATIBILITY
# =========================================================

app.add_url_rule(
    "/application-details/<int:candidate_id>",
    endpoint="details",
    view_func=application_details
)


# =========================================================
# RANKING
# =========================================================

@app.route("/ranking")
def ranking():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    candidates = get_ranked_candidates()

    return render_template(
        "ranking.html",

        candidates=candidates
    )


# =========================================================
# RANKING COMPATIBILITY
# =========================================================

app.add_url_rule(
    "/ranking",
    endpoint="rankings",
    view_func=ranking
)


# =========================================================
# EDIT CANDIDATE
# =========================================================

@app.route(
    "/edit/<int:id>"
)
def edit_candidate(id):

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    candidate = get_candidate_by_id(
        id
    )

    if not candidate:

        return "Candidate not found"

    return render_template(
        "edit.html",

        candidate=candidate
    )


# =========================================================
# EDIT COMPATIBILITY ENDPOINT
# =========================================================

app.add_url_rule(
    "/edit/<int:id>",
    endpoint="edit",
    view_func=edit_candidate
)


# =========================================================
# UPDATE CANDIDATE
# =========================================================

@app.route(
    "/update/<int:id>",
    methods=["POST"]
)
def update_candidate_route(id):

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    score = request.form.get(
        "score",
        0
    )

    status = request.form.get(
        "status",
        "Rejected"
    )


    # -----------------------------------------------------
    # SCORE CONVERSION
    # -----------------------------------------------------

    try:

        score = float(
            score
        )

    except (
        ValueError,
        TypeError
    ):

        score = 0


    # -----------------------------------------------------
    # SCORE LIMIT
    # -----------------------------------------------------

    if score < 0:

        score = 0

    if score > 100:

        score = 100


    # -----------------------------------------------------
    # STATUS VALIDATION
    # -----------------------------------------------------

    if status not in [
        "Selected",
        "Rejected"
    ]:

        status = "Rejected"


    # -----------------------------------------------------
    # UPDATE DATABASE
    # -----------------------------------------------------

    try:

        update_candidate(
            id,
            name,
            email,
            phone,
            score,
            status
        )

    except TypeError:

        try:

            update_candidate(
                id,
                name,
                email,
                phone
            )

        except Exception as e:

            return (
                "Database update error: "
                + str(e)
            )

    except Exception as e:

        return (
            "Database update error: "
            + str(e)
        )


    return redirect(
        url_for("dashboard")
    )


# =========================================================
# UPDATE COMPATIBILITY ENDPOINT
# =========================================================

app.add_url_rule(
    "/update/<int:id>",
    endpoint="update",
    view_func=update_candidate_route,
    methods=["POST"]
)


# =========================================================
# DELETE CANDIDATE
# =========================================================

@app.route(
    "/delete/<int:id>"
)
def delete_candidate_route(id):

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    try:

        delete_candidate(
            id
        )

    except Exception as e:

        return (
            "Database delete error: "
            + str(e)
        )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# DELETE COMPATIBILITY ENDPOINT
# =========================================================

app.add_url_rule(
    "/delete/<int:id>",
    endpoint="delete",
    view_func=delete_candidate_route
)


# =========================================================
# RESUME FILE
# =========================================================

@app.route(
    "/uploads/<path:filename>"
)
def uploaded_file(filename):

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# =========================================================
# UPLOADED FILE COMPATIBILITY
# =========================================================

app.add_url_rule(
    "/uploads/<path:filename>",
    endpoint="view_resume",
    view_func=uploaded_file
)


# =========================================================
# EXPORT CSV
# =========================================================

@app.route("/export")
def export():

    if not is_admin_logged_in():

        return redirect(
            url_for("admin")
        )

    candidates = get_all_candidates()

    output = io.StringIO()

    writer = csv.writer(
        output
    )


    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    writer.writerow([
        "ID",
        "Name",
        "Email",
        "Phone",
        "Resume",
        "Score",
        "Status",
        "Applied At",
        "TF-IDF Score",
        "Skill Score",
        "Matched Skills",
        "Missing Skills"
    ])


    # -----------------------------------------------------
    # DATA
    # -----------------------------------------------------

    for candidate in candidates:

        row = [
            candidate[0],
            candidate[1],
            candidate[2],
            candidate[3],
            candidate[4],
            candidate[5],
            candidate[6]
        ]


        # -------------------------------------------------
        # APPLIED AT
        # -------------------------------------------------

        if len(candidate) > 7:

            row.append(
                candidate[7]
            )

        else:

            row.append(
                ""
            )


        # -------------------------------------------------
        # TF-IDF SCORE
        # -------------------------------------------------

        if len(candidate) > 8:

            row.append(
                candidate[8]
            )

        else:

            row.append(
                ""
            )


        # -------------------------------------------------
        # SKILL SCORE
        # -------------------------------------------------

        if len(candidate) > 9:

            row.append(
                candidate[9]
            )

        else:

            row.append(
                ""
            )


        # -------------------------------------------------
        # MATCHED SKILLS
        # -------------------------------------------------

        if len(candidate) > 10:

            row.append(
                candidate[10]
            )

        else:

            row.append(
                ""
            )


        # -------------------------------------------------
        # MISSING SKILLS
        # -------------------------------------------------

        if len(candidate) > 11:

            row.append(
                candidate[11]
            )

        else:

            row.append(
                ""
            )


        writer.writerow(
            row
        )


    csv_data = output.getvalue()

    output.close()


    return Response(

        csv_data,

        mimetype="text/csv",

        headers={
            "Content-Disposition":
            "attachment; filename=candidates.csv"
        }
    )


# =========================================================
# ERROR HANDLER - 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <h1>404 - Page Not Found</h1>
    <p>The requested page does not exist.</p>
    """, 404


# =========================================================
# ERROR HANDLER - 500
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    return """
    <h1>500 - Internal Server Error</h1>
    <p>Something went wrong in the application.</p>
    """, 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(
        debug=False,
        host="0.0.0.0",
        port=port
    )