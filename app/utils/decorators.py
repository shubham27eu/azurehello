from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from app.models import User # Assuming User model can be imported

def role_required(*roles):
    """
    Decorator to ensure the current user has one of the specified roles.
    Assumes JWT authentication is used and user ID is the identity.
    The User model must have a 'role' attribute.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request() # Ensures JWT is present and valid
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)

            if not user:
                return jsonify(message="User not found"), 404

            if user.role not in roles:
                return jsonify(message=f"Access forbidden: User does not have required role(s) ({', '.join(roles)})"), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
