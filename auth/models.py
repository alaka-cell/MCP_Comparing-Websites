import sqlite3
import logging
from datetime import datetime
from .utils import hash_password, verify_password
import os

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DATABASE_URL", "auth.db")


def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with the users table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise


def register_user(username: str, password: str, role: str = 'user') -> dict:
    """
    Register a new user.
    Returns a dict with 'success' and 'message' keys.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "message": "Username already exists"}
        
        # Hash password and create user
        hashed_pw = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
            (username, hashed_pw, role)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"User registered successfully: {username}")
        return {"success": True, "message": "User registered successfully"}
    
    except Exception as e:
        logger.error(f"Error registering user {username}: {str(e)}", exc_info=True)
        return {"success": False, "message": f"Registration failed: {str(e)}"}


def get_user_by_username(username: str):
    """
    Retrieve a user by username.
    Returns dict with user data or None.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    except Exception as e:
        logger.error(f"Error fetching user {username}: {str(e)}", exc_info=True)
        return None


def authenticate_user(username: str, password: str):
    """
    Authenticate a user by username and password.
    Returns user dict if valid, None otherwise.
    """
    try:
        user = get_user_by_username(username)
        if user and verify_password(password, user['password']):
            return user
        return None
    except Exception as e:
        logger.error(f"Error authenticating user {username}: {str(e)}", exc_info=True)
        return None