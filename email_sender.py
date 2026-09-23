import os
import smtplib
from email.message import EmailMessage


# =====================================================
# EMAIL SETTINGS
# =====================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.getenv("RESUME_SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("RESUME_SENDER_PASSWORD", "")


# =====================================================
# SEND EMAIL
# =====================================================

def send_candidate_email(
    candidate_email,
    candidate_name,
    score,
    status
):

    # -------------------------------------------------
    # CHECK EMAIL SETTINGS
    # -------------------------------------------------

    if not SENDER_EMAIL or not SENDER_PASSWORD:

        print("Email notification skipped.")
        print("Please configure RESUME_SENDER_EMAIL and RESUME_SENDER_PASSWORD.")

        return False


    # -------------------------------------------------
    # SELECT MESSAGE
    # -------------------------------------------------

    if status == "Selected":

        subject = "Application Update - Selected"

        body = f"""
Dear {candidate_name},

Thank you for applying.

We are pleased to inform you that your resume has been selected
based on the AI Resume Screening process.

AI Resume Match Score: {score:.2f}%

Status: Selected

Our team will contact you regarding the next steps.

Regards,
AI Resume Screening System
"""

    else:

        subject = "Application Update - Resume Screening"

        body = f"""
Dear {candidate_name},

Thank you for applying.

Your resume has been evaluated using our AI Resume Screening System.

AI Resume Match Score: {score:.2f}%

Status: Rejected

We appreciate your interest and wish you success in your future opportunities.

Regards,
AI Resume Screening System
"""


    # -------------------------------------------------
    # CREATE EMAIL
    # -------------------------------------------------

    message = EmailMessage()

    message["From"] = SENDER_EMAIL

    message["To"] = candidate_email

    message["Subject"] = subject

    message.set_content(body)


    # -------------------------------------------------
    # SEND EMAIL
    # -------------------------------------------------

    try:

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                SENDER_EMAIL,
                SENDER_PASSWORD
            )

            server.send_message(message)


        print(
            f"Email sent successfully to {candidate_email}"
        )

        return True


    except Exception as e:

        print(
            f"Email sending failed: {e}"
        )

        return False