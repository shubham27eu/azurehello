from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required"}), 400

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'student') # Default role

    user = AuthService.register_user(username, password, email=email, role=role)
    if user:
        return jsonify({"message": "User registered successfully", "user": user.to_dict(include_email=True)}), 201
    # More specific error messages would be good here if AuthService returns them
    return jsonify({"message": "Registration failed (username or email may already exist)"}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required"}), 400

    username = data.get('username')
    password = data.get('password')

    result = AuthService.login_user(username, password)
    if result and result.get("access_token"):
        return jsonify(result), 200 # result includes token and user dict
    return jsonify({"message": "Invalid username or password"}), 401

# For a stateless JWT logout, client just discards the token.
# If using refresh tokens and a denylist/blocklist for access tokens:
# @auth_bp.route('/logout', methods=['POST'])
# @jwt_required()
# def logout():
#     try:
#         jti = get_jwt()['jti']
#         AuthService.add_token_to_blacklist(jti) # Requires implementation in AuthService
#         return jsonify(message="Successfully logged out"), 200
#     except Exception as e:
#         return jsonify(message=f"Logout failed: {str(e)}"), 500

# Simple logout - client side should remove token
@auth_bp.route('/logout', methods=['POST'])
@jwt_required() # Ensures a valid token is present to "logout"
def logout_placeholder():
    # In a stateless JWT setup, true logout is handled client-side by deleting the token.
    # This endpoint can be used to acknowledge the action or if a server-side denylist is implemented.
    return jsonify(message="Logout acknowledged. Client should discard token."), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    current_user_id = get_jwt_identity()
    user = AuthService.get_user_by_id(current_user_id)
    if user:
        return jsonify(user.to_dict(include_email=True)), 200
    return jsonify(message="User not found"), 404
