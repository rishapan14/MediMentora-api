"""Routes for AI Medical Teacher — Modules 1–2."""

from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import medical_teacher_controller as ctrl

medical_teacher_bp = Blueprint("medical_teacher", __name__, url_prefix="/api/medical-teacher")

# Module 1 — Document Processing
medical_teacher_bp.add_url_rule(
  "/books/upload",
  view_func=jwt_required()(ctrl.upload_books),
  methods=["POST"],
)
medical_teacher_bp.add_url_rule(
  "/books/upload-and-extract",
  view_func=jwt_required()(ctrl.upload_and_extract),
  methods=["POST"],
)
medical_teacher_bp.add_url_rule(
  "/books",
  view_func=jwt_required()(ctrl.list_books),
  methods=["GET"],
)
medical_teacher_bp.add_url_rule(
  "/books/<int:book_id>",
  view_func=jwt_required()(ctrl.get_book),
  methods=["GET"],
)
medical_teacher_bp.add_url_rule(
  "/books/<int:book_id>/extract",
  view_func=jwt_required()(ctrl.extract_book),
  methods=["POST"],
)
medical_teacher_bp.add_url_rule(
  "/books/<int:book_id>",
  view_func=jwt_required()(ctrl.delete_book),
  methods=["DELETE"],
)

# Module 2 — Book Parser
medical_teacher_bp.add_url_rule(
  "/books/<int:book_id>/parse",
  view_func=jwt_required()(ctrl.parse_book),
  methods=["POST"],
)
medical_teacher_bp.add_url_rule(
  "/books/<int:book_id>/chapters",
  view_func=jwt_required()(ctrl.list_chapters),
  methods=["GET"],
)
medical_teacher_bp.add_url_rule(
  "/books/<int:book_id>/chapters/<int:chapter_id>",
  view_func=jwt_required()(ctrl.get_chapter),
  methods=["GET"],
)
