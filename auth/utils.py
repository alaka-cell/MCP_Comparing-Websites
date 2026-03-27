import bcrypt
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "your_super_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt directly.
    Bcrypt has a 72-byte limit, so we truncate if necessary.
    """
    try:
        # CRITICAL: Truncate to 72 bytes BEFORE hashing
        password_bytes = password.encode('utf-8')[:72]
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}", exc_info=True)
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.
    Truncates to 72 bytes to match hashing behavior.
    """
    try:
        # Truncate to 72 bytes to match hashing behavior
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}", exc_info=True)
        return False


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token WITHOUT using python-jose.
    Uses simple JSON + base64 encoding.
    
    Args:
        data: Dictionary with claims to encode
        expires_delta: Optional timedelta for token expiration
    
    Returns:
        Encoded JWT token
    """
    try:
        import json
        import base64
        import hmac
        import hashlib
        
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire.timestamp()})
        
        # Header
        header = {"alg": "HS256", "typ": "JWT"}
        
        # Encode header and payload
        header_encoded = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip('=')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(to_encode, default=str).encode()
        ).decode().rstrip('=')
        
        # Create signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = base64.urlsafe_b64encode(
            hmac.new(
                SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode().rstrip('=')
        
        token = f"{message}.{signature}"
        logger.info(f"JWT token created successfully for user: {data.get('sub')}")
        return token
        
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}", exc_info=True)
        raise


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token WITHOUT using python-jose.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dict, or None if token is invalid
    """
    try:
        import json
        import base64
        import hmac
        import hashlib
        
        parts = token.split('.')
        if len(parts) != 3:
            logger.warning("Invalid token format")
            return None
        
        header_encoded, payload_encoded, signature_provided = parts
        
        # Add padding if needed
        padding = 4 - (len(payload_encoded) % 4)
        if padding != 4:
            payload_encoded += '=' * padding
        
        # Decode payload
        try:
            payload = json.loads(
                base64.urlsafe_b64decode(payload_encoded)
            )
        except Exception as e:
            logger.error(f"Error decoding payload: {str(e)}")
            return None
        
        # Verify signature
        message = f"{header_encoded}.{payload_encoded.rstrip('=')}"
        expected_signature = base64.urlsafe_b64encode(
            hmac.new(
                SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode().rstrip('=')
        
        if signature_provided != expected_signature:
            logger.warning("Invalid token signature")
            return None
        
        # Check expiration
        if "exp" in payload:
            if datetime.utcnow().timestamp() > payload["exp"]:
                logger.warning("Token expired")
                return None
        
        logger.info(f"Token decoded successfully for user: {payload.get('sub')}")
        return payload
        
    except Exception as e:
        logger.error(f"Error decoding access token: {str(e)}", exc_info=True)
        return None