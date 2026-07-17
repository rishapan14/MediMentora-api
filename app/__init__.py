import os

from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.config import Config
from app.extensions import db, jwt
from app.helpers.response import error_response
from app.routes import register_blueprints


def create_app():
  """Application factory."""
  app = Flask(__name__)
  app.config.from_object(Config)

  # Ensure upload directories exist
  os.makedirs(app.config["REPORT_UPLOAD_FOLDER"], exist_ok=True)
  os.makedirs(app.config["CERTIFICATE_UPLOAD_FOLDER"], exist_ok=True)

  db.init_app(app)
  jwt.init_app(app)
  CORS(app)

  # Import all models so SQLAlchemy registers metadata before create_all()
  from app.models import (  # noqa: F401
    CaseFavorite,
    Certificate,
    ClinicalCase,
    Comment,
    CommentLike,
    CompletedLesson,
    Course,
    Discussion,
    DiscussionLike,
    Lesson,
    LessonBookmark,
    Notification,
    Progress,
    Question,
    Quiz,
    Recommendation,
    Report,
    ReportAnalysis,
    Result,
    Simulation,
    SimulationAttempt,
    User,
  )

  @jwt.user_lookup_loader
  def user_lookup_callback(_jwt_header, jwt_data):
    from app.models.user_model import User as UserModel
    try:
      user_id = int(jwt_data["sub"])
    except (KeyError, TypeError, ValueError):
      return None
    return db.session.get(UserModel, user_id)

  register_blueprints(app)

  @app.route("/", methods=["GET"])
  def api_home():
    from flask import jsonify
    return jsonify({
      "status": "success",
      "message": "AI-Powered Clinical Report Analysis & Nursing Assistance Platform API",
      "data": {
        "version": "1.0.0",
        "modules": {
          "auth": "/api/auth",
          "reports": "/api/reports",
          "analysis": "/api/analysis",
          "learning": "/api/learning",
          "clinical_cases": "/api/clinical-cases",
          "simulations": "/api/simulations",
          "quizzes": "/api/quizzes",
          "progress": "/api/progress",
          "certificates": "/api/certificates",
          "discussions": "/api/discussions",
          "notifications": "/api/notifications",
        },
      },
    })

  @app.errorhandler(400)
  def bad_request(err):
    return error_response(getattr(err, "description", "Bad request."), 400)

  @app.errorhandler(404)
  def not_found(err):
    return error_response("Resource not found.", 404)

  @app.errorhandler(405)
  def method_not_allowed(err):
    return error_response("Method not allowed.", 405)

  @app.errorhandler(OperationalError)
  def handle_operational_error(err):
    db.session.rollback()
    orig = getattr(err, "orig", None)
    code = orig.args[0] if orig and orig.args else None
    if code == 1049:
      return error_response("Invalid database name configured.", 500)
    if code in (2003, 2002):
      return error_response("MySQL server is not running or not reachable.", 503)
    return error_response("Database connection failed.", 500)

  @app.errorhandler(ProgrammingError)
  def handle_programming_error(err):
    db.session.rollback()
    return error_response("Database schema error.", 500)

  @app.errorhandler(500)
  def handle_internal_error(err):
    db.session.rollback()
    return error_response("An internal server error occurred.", 500)

  return app
