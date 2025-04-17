import logging
import os
from flask import Blueprint, request
from flask_restx import Resource, fields
from services.utils.db_utils import get_db_connection, execute_query, execute_update, close_cursor, close_connection
from services.utils.auth_utils import hash_password, verify_password, generate_token

# Create a Blueprint for user routes
user_bp = Blueprint('users', __name__)

# Create a namespace for users
ns = None  # Will be initialized in init_app

# Define models for Swagger documentation
user_model = None
user_input_model = None
login_input_model = None
login_response_model = None

class UserRegistration(Resource):
    def post(self):
        """Register a new user"""
        conn = None
        cursor = None
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['username', 'password']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return {'status': 'error', 'message': f'Missing required fields: {", ".join(missing_fields)}'}, 400

            # Validate password length
            if len(data['password']) < 6:
                return {'status': 'error', 'message': 'Password must be at least 6 characters long'}, 400

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
                return {'status': 'error', 'message': 'Username already exists'}, 400

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

            return {
                'status': 'success',
                'message': 'User registered successfully',
                'data': {
                    'id': user[0],
                    'username': user[1]
                }
            }, 201

        except Exception as e:
            print(f"Error: {e}", flush=True)
            logging.error(f"Error: {e}")
            logging.exception("An unexpected error occurred")
            return {'status': 'error', 'message': 'An unexpected error occurred'}, 500
        finally:
            if cursor:
                close_cursor(cursor)
            if conn:
                close_connection(conn)

class UserLogin(Resource):
    def post(self):
        """Login user and return JWT token"""
        conn = None
        cursor = None
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data or 'username' not in data or 'password' not in data:
                return {'status': 'error', 'message': 'Username and password are required'}, 400

            # Get database connection
            conn = get_db_connection()

            # Get user by username
            cursor = execute_query(conn,
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (data['username'],)
            )
            user = cursor.fetchone()

            if not user or not verify_password(user[2], data['password']):
                return {'status': 'error', 'message': 'Invalid username or password'}, 401

            # Generate token
            token = generate_token(user[0])

            return {
                'status': 'success',
                'message': 'Login successful',
                'data': {
                    'token': token,
                    'user': {
                        'id': user[0],
                        'username': user[1]
                    }
                }
            }, 200

        except Exception as e:
            print(f"Error: {e}", flush=True)
            logging.error(f"Error: {e}")
            logging.exception("An unexpected error occurred")
            return {'status': 'error', 'message': 'An unexpected error occurred'}, 500
        finally:
            if cursor:
                close_cursor(cursor)
            if conn:
                close_connection(conn)

def init_app(api):
    global ns, user_model, user_input_model, login_input_model, login_response_model
    
    # Create a namespace for users with the correct path
    ns = api.namespace('users', description='User operations', path='/api/users')

    # Define models for Swagger documentation
    user_model = api.model('User', {
        'id': fields.Integer(readonly=True, description='The user unique identifier'),
        'username': fields.String(required=True, description='The username')
    })

    user_input_model = api.model('UserInput', {
        'username': fields.String(required=True, description='The username'),
        'password': fields.String(required=True, description='The password')
    })

    login_input_model = api.model('LoginInput', {
        'username': fields.String(required=True, description='The username'),
        'password': fields.String(required=True, description='The password')
    })

    login_response_model = api.model('LoginResponse', {
        'token': fields.String(description='JWT token'),
        'user': fields.Nested(user_model)
    })

    # Register routes and add Swagger documentation
    ns.add_resource(UserRegistration, '/register')
    ns.add_resource(UserLogin, '/login')
    
    # Add Swagger documentation to UserRegistration
    ns.doc('register_user', security=None)(UserRegistration.post)
    ns.expect(user_input_model)(UserRegistration.post)
    ns.response(201, 'User registered successfully', user_model)(UserRegistration.post)
    ns.response(400, 'Bad Request')(UserRegistration.post)
    ns.response(500, 'Internal Server Error')(UserRegistration.post)
    
    # Add Swagger documentation to UserLogin
    ns.doc('login_user', security=None)(UserLogin.post)
    ns.expect(login_input_model)(UserLogin.post)
    ns.response(200, 'Login successful', login_response_model)(UserLogin.post)
    ns.response(400, 'Bad Request')(UserLogin.post)
    ns.response(401, 'Invalid credentials')(UserLogin.post)
    ns.response(500, 'Internal Server Error')(UserLogin.post) 