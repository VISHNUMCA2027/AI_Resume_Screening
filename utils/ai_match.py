from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


# ==========================================
# SKILL WEIGHTS
# ==========================================

SKILL_WEIGHTS = {
    "python": 20,
    "flask": 10,
    "django": 10,
    "rest api": 8,
    "api": 6,
    "mysql": 8,
    "sqlite": 5,
    "sql": 5,
    "html": 4,
    "css": 4,
    "javascript": 4,
    "git": 4,
    "github": 4,
    "postman": 3,
    "oop": 3,
    "database": 3,
    "testing": 3,
    "debugging": 3,
    "problem solving": 3,
    "communication": 2,
    "teamwork": 2
}


# ==========================================
# TEXT PREPROCESSING
# ==========================================

def preprocess(text):
    """
    Convert text into clean lowercase format.
    """

    if not text:
        return ""

    text = text.lower()

    # Remove special characters
    text = re.sub(
        r"[^a-z0-9 ]",
        " ",
        text
    )

    # Remove extra spaces
    text = " ".join(text.split())

    return text


# ==========================================
# RESUME ANALYSIS
# ==========================================

def analyze_resume(resume_text, job_description):
    """
    Analyze resume against job description.

    Scoring:
        TF-IDF similarity      = 50%
        Weighted skill match   = 50%

    Returns:
        score
        tfidf_score
        skill_score
        matched_skills
        missing_skills
        job_skills
    """

    # ======================================
    # PREPROCESS TEXT
    # ======================================

    resume = preprocess(resume_text)
    jd = preprocess(job_description)


    # ======================================
    # 1. TF-IDF SIMILARITY - 50%
    # ======================================

    if not resume or not jd:

        similarity = 0

    else:

        vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        vectors = vectorizer.fit_transform(
            [resume, jd]
        )

        similarity = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]


    # Convert similarity into 50 marks
    tfidf_score = similarity * 50


    # ======================================
    # 2. FIND JOB SKILLS
    # ======================================

    jd_skills = []
    matched_skills = []
    missing_skills = []


    for skill in SKILL_WEIGHTS:

        # Skill exists in job description
        if skill in jd:

            jd_skills.append(skill)

            # Skill also exists in resume
            if skill in resume:

                matched_skills.append(skill)

            else:

                missing_skills.append(skill)


    # ======================================
    # 3. WEIGHTED SKILL SCORE - 50%
    # ======================================

    if len(jd_skills) > 0:

        # Total weight of skills required by job
        total_weight = sum(
            SKILL_WEIGHTS[skill]
            for skill in jd_skills
        )

        # Weight of skills candidate has
        matched_weight = sum(
            SKILL_WEIGHTS[skill]
            for skill in matched_skills
        )

        # Convert into 50 marks
        skill_score = (
            matched_weight
            / total_weight
        ) * 50

    else:

        skill_score = 0


    # ======================================
    # 4. FINAL SCORE
    # ======================================

    final_score = (
        tfidf_score
        + skill_score
    )


    # Maximum score = 100
    final_score = min(
        final_score,
        100
    )


    # ======================================
    # 5. RETURN COMPLETE ANALYSIS
    # ======================================

    return {

        "score": round(
            final_score,
            2
        ),

        "tfidf_score": round(
            tfidf_score,
            2
        ),

        "skill_score": round(
            skill_score,
            2
        ),

        "matched_skills":
            matched_skills,

        "missing_skills":
            missing_skills,

        "job_skills":
            jd_skills
    }


# ==========================================
# CALCULATE MATCH
# ==========================================
# app.py currently uses this function.
# So we keep it for compatibility.


def calculate_match(
    resume_text,
    job_description
):

    result = analyze_resume(
        resume_text,
        job_description
    )

    return result["score"]