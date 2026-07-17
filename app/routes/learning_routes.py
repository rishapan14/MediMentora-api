from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers import learning_controller as ctrl
from app.middleware import roles_required
from app.constants import ROLE_ADMIN, ROLE_DOCTOR

learning_bp = Blueprint("learning", __name__, url_prefix="/api/learning")

# Courses
learning_bp.add_url_rule("/courses", view_func=jwt_required()(ctrl.list_courses), methods=["GET"])
learning_bp.add_url_rule("/courses/<int:course_id>", view_func=jwt_required()(ctrl.get_course), methods=["GET"])
learning_bp.add_url_rule(
  "/courses",
  view_func=roles_required(ROLE_ADMIN, ROLE_DOCTOR)(ctrl.create_course),
  methods=["POST"],
)
learning_bp.add_url_rule(
  "/courses/<int:course_id>",
  view_func=roles_required(ROLE_ADMIN, ROLE_DOCTOR)(ctrl.update_course),
  methods=["PUT"],
)
learning_bp.add_url_rule(
  "/courses/<int:course_id>",
  view_func=roles_required(ROLE_ADMIN, ROLE_DOCTOR)(ctrl.delete_course),
  methods=["DELETE"],
)

# Lessons
learning_bp.add_url_rule("/courses/<int:course_id>/lessons", view_func=jwt_required()(ctrl.list_lessons), methods=["GET"])
learning_bp.add_url_rule(
  "/lessons",
  view_func=roles_required(ROLE_ADMIN, ROLE_DOCTOR)(ctrl.create_lesson),
  methods=["POST"],
)
learning_bp.add_url_rule(
  "/lessons/<int:lesson_id>",
  view_func=roles_required(ROLE_ADMIN, ROLE_DOCTOR)(ctrl.update_lesson),
  methods=["PUT"],
)
learning_bp.add_url_rule(
  "/lessons/<int:lesson_id>",
  view_func=roles_required(ROLE_ADMIN, ROLE_DOCTOR)(ctrl.delete_lesson),
  methods=["DELETE"],
)

# Bookmarks
learning_bp.add_url_rule("/bookmarks", view_func=jwt_required()(ctrl.list_bookmarks), methods=["GET"])
learning_bp.add_url_rule("/lessons/<int:lesson_id>/bookmark", view_func=jwt_required()(ctrl.add_bookmark), methods=["POST"])
learning_bp.add_url_rule("/lessons/<int:lesson_id>/bookmark", view_func=jwt_required()(ctrl.remove_bookmark), methods=["DELETE"])

# Completed lessons
learning_bp.add_url_rule("/lessons/<int:lesson_id>/complete", view_func=jwt_required()(ctrl.complete_lesson), methods=["POST"])
learning_bp.add_url_rule("/completed-lessons", view_func=jwt_required()(ctrl.list_completed_lessons), methods=["GET"])

# Recommendations & weak topics
learning_bp.add_url_rule("/recommendations", view_func=jwt_required()(ctrl.list_recommendations), methods=["GET"])
learning_bp.add_url_rule("/weak-topics", view_func=jwt_required()(ctrl.weak_topics), methods=["GET"])
