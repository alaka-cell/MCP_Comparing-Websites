from flask import Blueprint, request, jsonify, session
from .models import register_user, get_user_by_username, authenticate_user
from .utils import verify_password, create_access_token, decode_access_token
import logging

router = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@router.route('/register', methods=['POST', 'OPTIONS'])
def register():
    """Register a new user"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user')

        # Validation
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        if len(password) > 128:
            return jsonify({"error": "Password is too long (max 128 characters)"}), 400

        logger.info(f"Attempting to register user: {username}")
        result = register_user(username, password, role)

        if not result["success"]:
            logger.warning(f"Registration failed for {username}: {result['message']}")
            return jsonify({"error": result["message"]}), 400

        session.permanent = True
        session['username'] = username
        session['role'] = role

        logger.info(f"User registered successfully: {username}")
        return jsonify({
            "message": "Registration successful",
            "logged_in": True,
            "username": username,
            "role": role
        }), 200

    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@router.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """Login user and return JWT token"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', 'user')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        logger.info(f"Login attempt for user: {username}")
        user = get_user_by_username(username)

        if not user:
            logger.warning(f"Login failed - user not found: {username}")
            return jsonify({"error": "User not found"}), 401
        
        # Use verify_password from utils
        if not verify_password(password, user['password']):
            logger.warning(f"Login failed - invalid password for: {username}")
            return jsonify({"error": "Invalid password"}), 401
        
        if user['role'] != role:
            logger.warning(f"Login failed - role mismatch for {username}: expected {user['role']}, got {role}")
            return jsonify({"error": f"Invalid role. User is registered as {user['role']}"}), 401

        session.permanent = True
        session['username'] = username
        session['role'] = user['role']

        # Create JWT token
        access_token = create_access_token(data={"sub": username, "role": user['role']})

        logger.info(f"User logged in successfully: {username}")
        return jsonify({
            "logged_in": True,
            "username": username,
            "role": user['role'],
            "access_token": access_token,
            "token_type": "bearer"
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@router.route('/check_session', methods=['GET', 'OPTIONS'])
def check_session():
    """Check if user has an active session"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        token = None
        username = None
        role = None

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            payload = decode_access_token(token)
            if payload:
                username = payload.get('sub')
                role = payload.get('role')

        # Fallback to session
        if not username and 'username' in session:
            username = session['username']
            role = session.get('role', 'user')

        if username:
            return jsonify({
                "logged_in": True,
                "username": username,
                "role": role
            }), 200
        
        return jsonify({"logged_in": False, "username": None, "role": None}), 200

    except Exception as e:
        logger.error(f"Session check error: {str(e)}", exc_info=True)
        return jsonify({"logged_in": False, "error": str(e)}), 200


@router.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Logout user and clear session"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        username = session.get('username', 'unknown')
        session.clear()
        logger.info(f"User logged out: {username}")
        return jsonify({"message": "Logged out successfully"}), 200

    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500