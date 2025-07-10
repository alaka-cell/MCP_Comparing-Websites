from flask import Blueprint, request, jsonify, session
from auth.models import register_user, get_user_by_username
from auth.utils import verify_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "user")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    result = register_user(username, password, role)
    if result["success"]:
        return jsonify({"message": result["message"]}), 201
    else:
        return jsonify({"error": result["message"]}), 409

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    requested_role = data.get("role")

    if not username or not password or not requested_role:
        return jsonify({"error": "Username, password, and role are required"}), 400

    user = get_user_by_username(username)
    if user and verify_password(password, user.password) and user.role == requested_role:
        session["username"] = username
        session["role"] = user.role
        return jsonify({"message": "Login successful", "role": user.role}), 200
    else:
        return jsonify({"error": "Invalid credentials or role mismatch"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@auth_bp.route("/check_session", methods=["GET"])
def check_session():
    if "username" in session:
        return jsonify({
            "logged_in": True,
            "username": session["username"],
            "role": session["role"]
        }), 200
    return jsonify({"logged_in": False}), 401
