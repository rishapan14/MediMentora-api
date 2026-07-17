from functools import wraps

from flask_jwt_extended import current_user, verify_jwt_in_request

from app.helpers.response import error_response


def roles_required(*roles):
    """Decorator to restrict route access to specific user roles."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if not current_user:
                return error_response("User not found.", 404)
            if current_user.role not in roles:
                return error_response("Access forbidden: insufficient permissions.", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
