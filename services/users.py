import os
from flask import Blueprint, request, jsonify
from services.utils.db_utils import get_db_connection, execute_query, execute_update, close_cursor, close_connection
from services.utils.auth_utils import hash_password, verify_password, generate_token

# Create a Blueprint for user routes
user_bp = Blueprint('users', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'password']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Validate password length
        if len(data['password']) < 6:
            return jsonify({
                'status': 'error',
                'message': 'Password must be at least 6 characters long'
            }), 400

        # Hash password
        hashed_password = hash_password(data['password'])

        # Get database connection
        conn = get_db_connection()

        # Check if username already exists
        cursor = execute_query(conn, 
            "SELECT id FROM users WHERE username = ?",
            (data['username'],)
        )
        if cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), 400

        # Insert new user
        cursor = execute_update(conn,
            """
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
            RETURNING id, username
            """,
            (data['username'], hashed_password)
        )
        user = cursor.fetchone()

        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'id': user[0],
                'username': user[1]
            }
        }), 201

    except Exception as e:
        print(f"Error: {e}", flush=True)
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)

@user_bp.route('/login', methods=['POST'])
def login():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Username and password are required'
            }), 400

        # Get database connection
        conn = get_db_connection()

        # Get user by username
        cursor = execute_query(conn,
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (data['username'],)
        )
        user = cursor.fetchone()

        if not user or not verify_password(user[2], data['password']):
            return jsonify({
                'status': 'error',
                'message': 'Invalid username or password'
            }), 401

        # Generate token
        token = generate_token(user[0])

        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'token': token,
                'user': {
                    'id': user[0],
                    'username': user[1]
                }
            }
        }), 200

    except Exception as e:
        print(f"Error: {e}", flush=True)
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn) 