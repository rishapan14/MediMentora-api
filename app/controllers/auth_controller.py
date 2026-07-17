from flask import request
from flask_jwt_extended import current_user, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.helpers.response import error_response, success_response
from app.services.auth_service import AuthService
from app.validations.auth_validation import (
  validate_forgot_password,
  validate_login,
  validate_register,
  validate_reset_password,
)


def register():
  data = request.get_json(silent=True)
  errors = validate_register(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  try:
    user = AuthService.register_user(
      email=data["email"],
      password=data["password"],
      full_name=data.get("full_name"),
      role=data.get("role"),
    )
    tokens = AuthService.create_tokens(user)
    return success_response(
      "User registered successfully.",
      {"user": user.to_dict(), **tokens},
      201,
    )
  except ValueError as exc:
    return error_response(str(exc), 400)
  except IntegrityError:
    db.session.rollback()
    return error_response("Email address already exists.", 409)
  except Exception:
    db.session.rollback()
    return error_response("Registration failed.", 500)


def login():
  data = request.get_json(silent=True)
  errors = validate_login(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  try:
    user = AuthService.authenticate(data["email"], data["password"])
    if not user:
      return error_response("Invalid email or password.", 401)
    tokens = AuthService.create_tokens(user)
    return success_response("Login successful.", {"user": user.to_dict(), **tokens})
  except PermissionError as exc:
    return error_response(str(exc), 403)
  except Exception:
    return error_response("Login failed.", 500)


def refresh():
  from flask_jwt_extended import create_access_token

  user_id = get_jwt_identity()
  return success_response("Token refreshed.", {"access_token": create_access_token(identity=user_id)})


def forgot_password():
  data = request.get_json(silent=True)
  errors = validate_forgot_password(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  result = AuthService.request_password_reset(data["email"])
  # Always return success to avoid email enumeration
  payload = {"message": "If the email exists, a reset link has been generated."}
  if result:
    payload["reset_link"] = result["reset_link"]  # Dev convenience; remove in production email flow
  return success_response("Password reset initiated.", payload)


def reset_password():
  data = request.get_json(silent=True)
  errors = validate_reset_password(data)
  if errors:
    return error_response("Validation failed.", 400, {"errors": errors})

  try:
    user = AuthService.reset_password(data["token"], data["password"])
    return success_response("Password reset successful.", {"user": user.to_dict()})
  except ValueError as exc:
    return error_response(str(exc), 400)


def profile():
  if request.method == "GET":
    return success_response("Profile retrieved.", {"user": current_user.to_dict()})

  data = request.get_json(silent=True) or {}
  try:
    user = AuthService.update_profile(current_user, data)
    return success_response("Profile updated.", {"user": user.to_dict()})
  except ValueError as exc:
    return error_response(str(exc), 400)


def logout():
  # JWT is stateless; client discards tokens. Endpoint provided for frontend consistency.
  return success_response("Logged out successfully.")
