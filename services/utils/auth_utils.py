import jwt
import datetime
import os
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

# Secret key for JWT - in production, this should be in environment variables
SECRET_KEY = os.getenv('SECRET_KEY')

def hash_password(password):
    """Hash a password for storing"""
    return generate_password_hash(password)

def verify_password(stored_hash, provided_password):
    """Verify a stored password against one provided by user"""
    return check_password_hash(stored_hash, provided_password)

def generate_token(user_id):
    """Generate a JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def verify_token(token):
    """Verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid token format'
                }), 401

        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Token is missing'
            }), 401

        user_id = verify_token(token)
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'Invalid or expired token'
            }), 401

        # Add user_id to the function's arguments
        return f(*args, user_id=user_id, **kwargs)

    return decorated 