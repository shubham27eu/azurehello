from app import db # db instance
from app.models import User
from flask_jwt_extended import create_access_token
from app.services.audit_logging_service import AuditLoggingService # Import AuditLoggingService
# from datetime import timedelta # If using token expiry configuration

class AuthService:
    @staticmethod
    def register_user(username, password, email=None, role='student'):
        if User.query.filter_by(username=username).first():
            # Consider raising a custom exception or returning a specific error object
            return None  # Username already exists
        if email and User.query.filter_by(email=email).first():
            return None # Email already exists

        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        AuditLoggingService.log_event(action="USER_REGISTER_SUCCESS", acting_user_id=user.id, target_user_id=user.id, status_outcome="SUCCESS", details={"username": user.username, "role": user.role, "email": user.email})
        return user

    @staticmethod
    def login_user(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # identity for JWT sub claim should be a string
            access_token = create_access_token(identity=str(user.id))
            AuditLoggingService.log_event(action="USER_LOGIN_SUCCESS", acting_user_id=user.id, status_outcome="SUCCESS", details={"username": username})
            return {"access_token": access_token, "user": user.to_dict()}

        AuditLoggingService.log_event(action="USER_LOGIN_FAILURE", status_outcome="FAILURE", details={"username_attempted": username, "reason": "Invalid credentials"})
        return None

    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)

    # Placeholder for token blacklisting if implementing full logout
    # revoked_tokens = set() # In-memory for demo; use Redis/DB for production
    # @staticmethod
    # def add_token_to_blacklist(jti):
    #     AuthService.revoked_tokens.add(jti)

    # @staticmethod
    # def is_token_revoked(jwt_payload):
    #     jti = jwt_payload['jti']
    #     return jti in AuthService.revoked_tokens

# JWT related callbacks (optional, can be in __init__.py or here)
# from app import jwt
# @jwt.token_in_blocklist_loader # Using blocklist for logout
# def check_if_token_in_blocklist(jwt_header, jwt_payload):
#     return AuthService.is_token_revoked(jwt_payload)

# @jwt.user_lookup_loader
# def user_lookup_callback(_jwt_header, jwt_data):
#     identity = jwt_data["sub"]
#     return User.query.get(identity)
