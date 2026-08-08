import os
from datetime import timedelta
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    """Read a comma-separated environment variable into clean values."""
    return tuple(value.strip().rstrip("/") for value in os.getenv(name, default).split(",") if value.strip())


class Config:
    """Application configuration loaded from environment variables."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:5000").rstrip("/")
    CORS_ORIGINS = _csv_env(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,https://medimentora-client.vercel.app",
    )

    # MySQL database
    # Support both this application's DB_* names and Railway MySQL's native
    # MYSQL* variables. Explicit DB_* values take precedence.
    DB_USER = os.getenv("DB_USER") or os.getenv("MYSQLUSER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD", "root123")
    DB_HOST = os.getenv("DB_HOST") or os.getenv("MYSQLHOST", "localhost")
    DB_PORT = os.getenv("DB_PORT") or os.getenv("MYSQLPORT", "3306")
    DB_NAME = os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE", "clinical_platform_db")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "30"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
    )

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Gemini (AI Medical Teacher enrichment — optional; heuristic parser works without it)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    TEACHER_USE_AI = os.getenv("TEACHER_USE_AI", "true").lower() == "true"

    # File uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    REPORT_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "reports")
    CERTIFICATE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "certificates")
    XRAY_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "xrays")
    XRAY_HEATMAP_FOLDER = os.path.join(UPLOAD_FOLDER, "xrays", "heatmaps")
    XRAY_PREPROCESSED_FOLDER = os.path.join(UPLOAD_FOLDER, "xrays", "preprocessed")
    # Educational healthy reference library (Healthy X-Ray Comparison Module 2)
    XRAY_REFERENCE_LIBRARY_FOLDER = os.getenv(
      "XRAY_REFERENCE_LIBRARY_FOLDER", "reference_library"
    )
    XRAY_AUTO_SEED_REFERENCES = os.getenv("XRAY_AUTO_SEED_REFERENCES", "false").lower() == "true"
    # AI Medical Teacher — textbooks / notes / guidelines (Module 1)
    TEACHER_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "medical_teacher", "books")
    TEACHER_MAX_FILES = int(os.getenv("TEACHER_MAX_FILES", "5"))
    TEACHER_MAX_FILE_BYTES = int(os.getenv("TEACHER_MAX_FILE_BYTES", str(100 * 1024 * 1024)))  # 100 MB
    TEACHER_MAX_TOTAL_BYTES = int(os.getenv("TEACHER_MAX_TOTAL_BYTES", str(200 * 1024 * 1024)))
    TEACHER_ALLOWED_EXTENSIONS = ("pdf", "docx", "txt")
    # X-ray upload limits
    XRAY_MAX_FILES = int(os.getenv("XRAY_MAX_FILES", "20"))
    XRAY_MAX_FILE_BYTES = int(os.getenv("XRAY_MAX_FILE_BYTES", str(25 * 1024 * 1024)))  # 25 MB each
    XRAY_MAX_TOTAL_BYTES = int(os.getenv("XRAY_MAX_TOTAL_BYTES", str(100 * 1024 * 1024)))
    XRAY_MIN_WIDTH = int(os.getenv("XRAY_MIN_WIDTH", "64"))
    XRAY_MIN_HEIGHT = int(os.getenv("XRAY_MIN_HEIGHT", "64"))
    XRAY_MAX_WIDTH = int(os.getenv("XRAY_MAX_WIDTH", "10000"))
    XRAY_MAX_HEIGHT = int(os.getenv("XRAY_MAX_HEIGHT", "10000"))
    # Phase 1: JPG/JPEG/PNG + DICOM (.dcm / .dicom)
    XRAY_ALLOWED_EXTENSIONS = tuple(
      e.strip().lower()
      for e in os.getenv(
        "XRAY_ALLOWED_EXTENSIONS", "jpg,jpeg,png,dcm,dicom"
      ).split(",")
      if e.strip()
    )
    # X-ray preprocessing (Module 3)
    XRAY_PREPROCESS_MAX_DIM = int(os.getenv("XRAY_PREPROCESS_MAX_DIM", "2048"))
    XRAY_PREPROCESS_MIN_DIM = int(os.getenv("XRAY_PREPROCESS_MIN_DIM", "512"))
    XRAY_AUTO_PREPROCESS = os.getenv("XRAY_AUTO_PREPROCESS", "true").lower() == "true"
    # X-ray vision model (Module 4): auto | heuristic | onnx
    XRAY_VISION_MODEL = os.getenv("XRAY_VISION_MODEL", "auto")
    XRAY_VISION_ONNX_PATH = os.getenv("XRAY_VISION_ONNX_PATH", "")
    # X-ray heatmap (Module 6)
    XRAY_AUTO_HEATMAP = os.getenv("XRAY_AUTO_HEATMAP", "true").lower() == "true"
    # Educational healthy comparison (Comparison Module 3)
    XRAY_AUTO_COMPARISON = os.getenv("XRAY_AUTO_COMPARISON", "true").lower() == "true"
    # Multi-upload limits: up to 20 files / 100 MB total (request body limit)
    UPLOAD_MAX_FILES = int(os.getenv("UPLOAD_MAX_FILES", "20"))
    UPLOAD_MAX_TOTAL_BYTES = int(os.getenv("UPLOAD_MAX_TOTAL_BYTES", str(100 * 1024 * 1024)))
    UPLOAD_MAX_FILE_BYTES = int(os.getenv("UPLOAD_MAX_FILE_BYTES", str(100 * 1024 * 1024)))
    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", str(UPLOAD_MAX_TOTAL_BYTES + (2 * 1024 * 1024)))
    )

    # Password reset
    RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("RESET_TOKEN_EXPIRE_HOURS", "24"))

    # Frontend URL (for password reset links in emails — placeholder)
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # OCR pipeline (Module 1 — medical report analysis)
    OCR_ENGINE = os.getenv("OCR_ENGINE", "auto")
    OCR_PREPROCESS = os.getenv("OCR_PREPROCESS", "true").lower() == "true"
    OCR_TIMEOUT_SECONDS = int(os.getenv("OCR_TIMEOUT_SECONDS", "120"))
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")

    # Image enhancement (OpenCV) — binarize only helps Tesseract on clean scans
    IMAGE_ENHANCE_BINARIZE = os.getenv("IMAGE_ENHANCE_BINARIZE", "false").lower() == "true"
