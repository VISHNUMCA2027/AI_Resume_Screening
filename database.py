import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

# =========================================================
# DATABASE CONNECTION
# =========================================================

DATABASE = "resume.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE HELPERS
# =========================================================

def _column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def _add_column_if_missing(cursor, table_name, column_name, column_definition):
    if not _column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            filename TEXT,
            score REAL DEFAULT 0,
            status TEXT,
            applied_at TEXT,
            tfidf_score REAL DEFAULT 0,
            skill_score REAL DEFAULT 0,
            matched_skills TEXT DEFAULT '',
            missing_skills TEXT DEFAULT '',
            job_skills TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'candidate',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Migrate older resume.db files without deleting existing data.
    _add_column_if_missing(cursor, "candidates", "applied_at", "TEXT")
    _add_column_if_missing(cursor, "candidates", "tfidf_score", "REAL DEFAULT 0")
    _add_column_if_missing(cursor, "candidates", "skill_score", "REAL DEFAULT 0")
    _add_column_if_missing(cursor, "candidates", "matched_skills", "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "candidates", "missing_skills", "TEXT DEFAULT ''")
    _add_column_if_missing(cursor, "candidates", "job_skills", "TEXT DEFAULT ''")

    conn.commit()
    conn.close()


# =========================================================
# ADD APPLICATION DATE COLUMN
# =========================================================

def add_application_date_column():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _add_column_if_missing(cursor, "candidates", "applied_at", "TEXT")
        conn.commit()
    finally:
        conn.close()


# =========================================================
# ADD AI COLUMNS
# =========================================================

def add_ai_columns():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _add_column_if_missing(cursor, "candidates", "tfidf_score", "REAL DEFAULT 0")
        _add_column_if_missing(cursor, "candidates", "skill_score", "REAL DEFAULT 0")
        _add_column_if_missing(cursor, "candidates", "matched_skills", "TEXT DEFAULT ''")
        _add_column_if_missing(cursor, "candidates", "missing_skills", "TEXT DEFAULT ''")
        _add_column_if_missing(cursor, "candidates", "job_skills", "TEXT DEFAULT ''")
        conn.commit()
    finally:
        conn.close()


# =========================================================
# SAVE CANDIDATE / NEW APPLICATION
# =========================================================

def save_candidate(
    name,
    email,
    phone,
    filename,
    score,
    status,
    tfidf_score=0,
    skill_score=0,
    matched_skills=None,
    missing_skills=None,
    job_skills=None
):
    conn = get_connection()
    cursor = conn.cursor()

    applied_at = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    matched_text = ", ".join(matched_skills or [])
    missing_text = ", ".join(missing_skills or [])
    job_text = ", ".join(job_skills or [])

    cursor.execute("""
        INSERT INTO candidates
        (
            name, email, phone, filename, score, status, applied_at,
            tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        phone,
        filename,
        score,
        status,
        applied_at,
        tfidf_score,
        skill_score,
        matched_text,
        missing_text,
        job_text
    ))

    conn.commit()
    conn.close()


# =========================================================
# GET ALL CANDIDATES
# =========================================================

def get_all_candidates():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, phone, filename, score, status, applied_at,
               tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        FROM candidates
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


# =========================================================
# SEARCH CANDIDATES
# =========================================================

def search_candidates(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    search_value = f"%{keyword}%"

    cursor.execute("""
        SELECT id, name, email, phone, filename, score, status, applied_at,
               tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        FROM candidates
        WHERE name LIKE ?
           OR email LIKE ?
           OR phone LIKE ?
           OR status LIKE ?
           OR filename LIKE ?
        ORDER BY id DESC
    """, (
        search_value,
        search_value,
        search_value,
        search_value,
        search_value
    ))

    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


# =========================================================
# GET CANDIDATE BY ID
# =========================================================

def get_candidate_by_id(candidate_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, phone, filename, score, status, applied_at,
               tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        FROM candidates
        WHERE id = ?
    """, (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    return tuple(row) if row else None


# =========================================================
# UPDATE CANDIDATE
# =========================================================

def update_candidate(candidate_id, name, email, phone, score, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE candidates
        SET name = ?, email = ?, phone = ?, score = ?, status = ?
        WHERE id = ?
    """, (name, email, phone, score, status, candidate_id))
    conn.commit()
    conn.close()


# =========================================================
# DELETE CANDIDATE
# =========================================================

def delete_candidate(candidate_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    conn.commit()
    conn.close()


# =========================================================
# RANKED CANDIDATES
# =========================================================

def get_ranked_candidates():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, phone, filename, score, status, applied_at,
               tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        FROM candidates
        ORDER BY score DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


# =========================================================
# TOTAL CANDIDATE COUNT
# =========================================================

def get_total_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM candidates")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# =========================================================
# STATUS COUNT
# =========================================================

def get_status_count(status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM candidates WHERE status = ?", (status,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


# =========================================================
# PREVIOUS APPLICATION HISTORY
# =========================================================

def get_previous_applications(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, phone, filename, score, status, applied_at,
               tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        FROM candidates
        WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))
        ORDER BY id DESC
    """, (email,))
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


# =========================================================
# PREVIOUS APPLICATION COUNT
# =========================================================

def get_previous_application_count(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM candidates
        WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))
    """, (email,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


# =========================================================
# UPDATE APPLICATION STATUS
# =========================================================

def update_candidate_status(candidate_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE candidates
        SET status = ?
        WHERE id = ?
    """, (status, candidate_id))
    conn.commit()
    conn.close()


# =========================================================
# GET SELECTED CANDIDATES
# =========================================================

def get_selected_candidates():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, phone, filename, score, status, applied_at,
               tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        FROM candidates
        WHERE status = 'Selected'
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


# =========================================================
# GET REJECTED CANDIDATES
# =========================================================

def get_rejected_candidates():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, phone, filename, score, status, applied_at,
               tfidf_score, skill_score, matched_skills, missing_skills, job_skills
        FROM candidates
        WHERE status = 'Rejected'
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [tuple(row) for row in rows]


# =========================================================
# CANDIDATE USER ACCOUNTS
# =========================================================

def create_user(name, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (name, email, password_hash, role, created_at)
        VALUES (?, ?, ?, 'candidate', ?)
    """, (
        name,
        email.strip().lower(),
        generate_password_hash(password),
        datetime.now().strftime("%d-%m-%Y %I:%M %p")
    ))

    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, password_hash, role, created_at
        FROM users
        WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))
    """, (email,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, email, password_hash, role, created_at
        FROM users
        WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_applications(email):
    return get_previous_applications(email)


def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


# =========================================================
# RESET CANDIDATE PASSWORD
# =========================================================

def reset_user_password(email, new_password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET password_hash = ?
        WHERE LOWER(TRIM(email)) = LOWER(TRIM(?))
    """, (
        generate_password_hash(new_password),
        email
    ))

    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return changed


# =========================================================
# INITIALIZE DATABASE
# =========================================================

create_database()
add_application_date_column()
add_ai_columns()


if __name__ == "__main__":
    print("Database initialized successfully.")
