import datetime
import os
import logging
from flask import Flask, request, Blueprint
from flask_restx import Resource, fields
from dotenv import load_dotenv
from services.utils.db_utils import get_db_connection, execute_query, execute_update, close_cursor, close_connection
from services.utils.auth_utils import token_required

# Load environment variables from the correct path
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env', '.env'))

# Create a Blueprint for task routes
task_bp = Blueprint('tasks', __name__)

# Create a namespace for tasks
ns = None  # Will be initialized in init_app

# Create a separate namespace for health check
health_ns = None  # Will be initialized in init_app

# Define models for Swagger documentation
task_model = None
task_input_model = None

class HealthCheck(Resource):
    def get(self):
        """Check service health status"""
        return {
            'status': 'success',
            'message': 'Service is healthy',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }

def validate_task_data(data, required_fields=None):
    """Validate task data and return error response if invalid"""
    if not data:
        return ({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return ({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

    # Validate field types and values
    if 'title' in data and (not isinstance(data['title'], str) or len(data['title'].strip()) == 0):
        return ({
            'status': 'error',
            'message': 'Title must be a non-empty string'
        }), 400

    if 'description' in data and not isinstance(data['description'], str):
        return ({
            'status': 'error',
            'message': 'Description must be a string'
        }), 400

    if 'status' in data and data['status'] not in ['pending', 'in_progress', 'completed']:
        return ({
            'status': 'error',
            'message': 'Status must be one of: pending, in_progress, completed'
        }), 400

    return None

# @app.route("/api/tasks", methods=["GET", "POST"])
# def handle_tasks():
#     if request.method == "GET":
#         return get_tasks()
#     elif request.method == "POST":
#         return create_task()

class TaskList(Resource):
    @token_required
    def get(self, user_id):
        """List all tasks for a user"""
        conn = None
        cursor = None
        try:
            # Ensure user_id is the correct type
            logging.debug(f"Fetching tasks for user_id: {user_id}")
            if not isinstance(user_id, int):
                return {
                    'status': 'error',
                    'message': 'Invalid user ID'+ str(user_id)
                }, 400

            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            # Validate pagination parameters
            if page < 1 or per_page < 1:
                return {
                    'status': 'error',
                    'message': 'Page and per_page must be positive integers'
                }, 400

            # Calculate offset
            offset = (page - 1) * per_page

            # Get database connection
            conn = get_db_connection()

            # Get total count of tasks for the current user
            cursor = execute_query(conn,
                "SELECT COUNT(*) FROM tasks WHERE user_id = ?",
                (user_id,)
            )
            total_tasks = cursor.fetchone()[0]

            # Get paginated tasks for the current user
            cursor = execute_query(conn,
                """
                SELECT id, title, description, status, created_at, updated_at
                FROM tasks
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, per_page, offset)
            )
            tasks = cursor.fetchall()
            
            # Convert tasks to list of dictionaries that match the task_model
            task_list = [{
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'status': task[3],
                'created_at': task[4],
                'updated_at': task[5]
            } for task in tasks]
            
            return {
                'status': 'success',
                'data': {
                    'tasks': task_list,
                    'pagination': {
                        'total': total_tasks,
                        'page': page,
                        'per_page': per_page,
                        'total_pages': (total_tasks + per_page - 1) // per_page,
                        'has_next': page < (total_tasks + per_page - 1) // per_page,
                        'has_prev': page > 1
                    }
                }
            }, 200

        except Exception as e:
            logging.error(f"Error: {e}")
            print(f"Error: {e}", flush=True)
            api.logger.info(f"Error: {e}")
            api.logger.exception("An unexpected error occurred")
            return {
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, 500
        finally:
            if cursor:
                close_cursor(cursor)
            if conn:
                close_connection(conn)

    @token_required
    def post(self, user_id):
        """Create a new task"""
        conn = None
        cursor = None
        try:
            data = request.get_json()
            print(f"Current user: {user_id}", flush=True)
            
            # Validate task data using the validate_task_data function
            validation_result = validate_task_data(data, required_fields=['title', 'description'])
            if validation_result:
                return validation_result

            # Get database connection
            conn = get_db_connection()

            # Insert new task
            cursor = execute_update(conn,
                """
                INSERT INTO tasks (title, description, status, user_id, created_at, updated_at)
                VALUES (?, ?, 'pending', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                RETURNING id, title, description, status, created_at, updated_at
                """,
                (data['title'], data['description'], user_id)
            )
            task = cursor.fetchone()
            print(f"Task created: {task}", flush=True)
            
            # Format the response to match task_model
            response_data = {
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'status': task[3],
                'created_at': task[4],
                'updated_at': task[5]
            }
            
            return {
                'status': 'success',
                'message': 'Task created successfully',
                'data': response_data
            }, 201

        except Exception as e:
            print(f"Error: {e}", flush=True)
            logging.error(f"Error: {e}")
            api.logger.info(f"Error: {e}")
            api.logger.exception("An unexpected error occurred")
            return {
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, 500
        finally:
            if cursor:
                close_cursor(cursor)
            if conn:
                close_connection(conn)

class Task(Resource):
    @token_required
    def put(self, user_id, task_id):
        """Update a task"""
        conn = None
        cursor = None
        try:
            print(f"Current user: {user_id}", flush=True)
            print(f"Current task_id: {task_id}", flush=True)
         
            data = request.get_json()
            
            # Validate input data using validate_task_data function
            validation_result = validate_task_data(data)
            if validation_result:
                return validation_result
            
            # Get database connection
            conn = get_db_connection()

            # Check if task exists and belongs to the current user
            cursor = execute_query(conn,
                "SELECT id FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id)
            )
            if not cursor.fetchone():
                return {
                    'status': 'error',
                    'message': 'Task not found'
                }, 404

            # Update task
            cursor = execute_update(conn,
                """
                UPDATE tasks
                SET title = COALESCE(?, title),
                    description = COALESCE(?, description),
                    status = COALESCE(?, status),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                RETURNING id, title, description, status, created_at, updated_at
                """,
                (data.get('title'), data.get('description'), data.get('status'), task_id, user_id)
            )
            task = cursor.fetchone()
            
            if not task:
                return {
                    'status': 'error',
                    'message': 'Task not found'
                }, 404

            # Format the response to match task_model
            response_data = {
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'status': task[3],
                'created_at': task[4],
                'updated_at': task[5]
            }

            return {
                'status': 'success',
                'message': 'Task updated successfully',
                'data': response_data
            }, 200

        except Exception as e:
            logging.error(f"Error: {e}")
            api.logger.error(f"Error: {e}")
            return {
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, 500
        finally:
            if cursor:
                close_cursor(cursor)
            if conn:
                close_connection(conn)

    @token_required
    def delete(self, user_id, task_id):
        """Delete a task"""
        conn = None
        cursor = None
        try:
            # Get database connection
            conn = get_db_connection()

            # Delete task
            cursor = execute_update(conn,
                "DELETE FROM tasks WHERE id = ? AND user_id = ?",
                (task_id, user_id)
            )

            if cursor.rowcount == 0:
                return {
                    'status': 'error',
                    'message': 'Task not found'
                }, 404

            return {
                'status': 'success',
                'message': 'Task deleted successfully'
            }, 200

        except Exception as e:
            logging.error(f"Error: {e}")
            return {
                'status': 'error',
                'message': 'An unexpected error occurred'
            }, 500
        finally:
            if cursor:
                close_cursor(cursor)
            if conn:
                close_connection(conn)

def init_app(api):
    global ns, task_model, task_input_model
    
    # Create a namespace for tasks with the correct path
    ns = api.namespace('tasks', description='Task operations', path='/api/tasks')

    # Create a separate namespace for health check
    health_ns = api.namespace('health', description='Health check operations', path='/api/health')

    # Define models for Swagger documentation
    task_model = api.model('Task', {
        'id': fields.Integer(readonly=True, description='The task unique identifier'),
        'title': fields.String(required=True, description='The task title'),
        'description': fields.String(required=True, description='The task description'),
        'status': fields.String(description='The task status', enum=['pending', 'in_progress', 'completed']),
        'created_at': fields.DateTime(readonly=True, description='Task creation timestamp'),
        'updated_at': fields.DateTime(readonly=True, description='Task last update timestamp')
    })

    task_input_model = api.model('TaskInput', {
        'title': fields.String(required=True, description='The task title'),
        'description': fields.String(required=True, description='The task description'),
        'status': fields.String(description='The task status', enum=['pending', 'in_progress', 'completed'])
    })

    # Add authorization documentation
    authorizations = {
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Enter your JWT token in the format: Bearer your.jwt.token\n\nExample: Bearer token_here"
        }
    }

    # Add security to the API
    api.authorizations = authorizations
    api.security = 'Bearer Auth'

    # Register routes
    health_ns.add_resource(HealthCheck, '')
    ns.add_resource(TaskList, '')
    ns.add_resource(Task, '/<int:task_id>')
    
    # Add Swagger documentation to HealthCheck
    health_ns.doc('health_check', security=None)(HealthCheck.get)
    health_ns.response(200, 'Service is healthy')(HealthCheck.get)
    
    # Add Swagger documentation to TaskList
    ns.doc('list_tasks', 
        security='Bearer Auth',
        params={
            'page': {
                'description': 'Page number for pagination',
                'type': 'integer',
                'default': 1,
                'in': 'query'
            },
            'per_page': {
                'description': 'Number of items per page',
                'type': 'integer',
                'default': 10,
                'in': 'query'
            }
        }
    )(TaskList.get)
    ns.response(200, 'Success', task_model)(TaskList.get)
    ns.response(400, 'Bad Request')(TaskList.get)
    ns.response(401, 'Unauthorized')(TaskList.get)
    ns.response(500, 'Internal Server Error')(TaskList.get)
    
    ns.doc('create_task', security='Bearer Auth')(TaskList.post)
    ns.expect(task_input_model)(TaskList.post)
    ns.response(201, 'Task created successfully', task_model)(TaskList.post)
    ns.response(400, 'Bad Request')(TaskList.post)
    ns.response(401, 'Unauthorized')(TaskList.post)
    ns.response(500, 'Internal Server Error')(TaskList.post)
    
    # Add Swagger documentation to Task
    ns.doc('update_task', security='Bearer Auth')(Task.put)
    ns.expect(task_input_model)(Task.put)
    ns.response(200, 'Task updated successfully', task_model)(Task.put)
    ns.response(400, 'Bad Request')(Task.put)
    ns.response(401, 'Unauthorized')(Task.put)
    ns.response(404, 'Task not found')(Task.put)
    ns.response(500, 'Internal Server Error')(Task.put)
    
    ns.doc('delete_task', security='Bearer Auth')(Task.delete)
    ns.response(200, 'Task deleted successfully')(Task.delete)
    ns.response(401, 'Unauthorized')(Task.delete)
    ns.response(404, 'Task not found')(Task.delete)
    ns.response(500, 'Internal Server Error')(Task.delete)
