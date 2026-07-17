"""Application-wide constants."""

# User roles
ROLE_ADMIN = "admin"
ROLE_DOCTOR = "doctor"
ROLE_NURSE = "nurse"
ROLE_MEDICAL_STUDENT = "medical_student"

VALID_ROLES = [ROLE_ADMIN, ROLE_DOCTOR, ROLE_NURSE, ROLE_MEDICAL_STUDENT]

# Report file types
REPORT_TYPE_PDF = "pdf"
REPORT_TYPE_IMAGE = "image"

# Notification types
NOTIF_LEARNING_REMINDER = "learning_reminder"
NOTIF_QUIZ_REMINDER = "quiz_reminder"
NOTIF_CERTIFICATE = "certificate_notification"

# Difficulty levels
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"

VALID_DIFFICULTIES = [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]
