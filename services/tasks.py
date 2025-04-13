import datetime
import os
import logging
from flask import Flask, jsonify, request, Blueprint
from dotenv import load_dotenv
from services.utils.db_utils import get_db_connection, execute_query, execute_update, close_cursor, close_connection
from services.utils.auth_utils import token_required

# Load environment variables from the correct path
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env', '.env'))

app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))
print(f"Port: {port}")

# Create a Blueprint for task routes
task_bp = Blueprint('tasks', __name__)

def validate_task_data(data, required_fields=None):
    """Validate task data and return error response if invalid"""
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'No data provided'
        }), 400

    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

    # Validate field types and values
    if 'title' in data and (not isinstance(data['title'], str) or len(data['title'].strip()) == 0):
        return jsonify({
            'status': 'error',
            'message': 'Title must be a non-empty string'
        }), 400

    if 'description' in data and not isinstance(data['description'], str):
        return jsonify({
            'status': 'error',
            'message': 'Description must be a string'
        }), 400

    if 'status' in data and data['status'] not in ['pending', 'in_progress', 'completed']:
        return jsonify({
            'status': 'error',
            'message': 'Status must be one of: pending, in_progress, completed'
        }), 400

    return None

@app.route("/")
def home():
    return "Hello, this is a Flask Microservice" + " "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# @app.route("/api/tasks", methods=["GET", "POST"])
# def handle_tasks():
#     if request.method == "GET":
#         return get_tasks()
#     elif request.method == "POST":
#         return create_task()

@task_bp.route('/', methods=['GET'])
@token_required
def get_tasks(user_id):
    conn = None
    cursor = None
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Validate pagination parameters
        if page < 1 or per_page < 1:
            return jsonify({
                'status': 'error',
                'message': 'Page and per_page must be positive integers'
            }), 400

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
        return jsonify({
            'status': 'success',
            'data': {
                'tasks': [{
                    'id': task[0],
                    'title': task[1],
                    'description': task[2],
                    'status': task[3],
                    'created_at': task[4],
                    'updated_at': task[5]
                } for task in tasks],
                'pagination': {
                    'total': total_tasks,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_tasks + per_page - 1) // per_page,
                    'has_next': page < (total_tasks + per_page - 1) // per_page,
                    'has_prev': page > 1
                }
            }
        }), 200

    except Exception as e:
        logging.error(f"Error: {e}")
        print(f"Error: {e}", flush=True)
        app.logger.info(f"Error: {e}")
        app.logger.exception("An unexpected error occurred")

        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)

@task_bp.route('/', methods=['POST'])
@token_required
def create_task(user_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        print(f"Current user: {user_id}", flush=True)
        # Validate required fields
        required_fields = ['title', 'description']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

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
        return jsonify({
            'status': 'success',
            'message': 'Task created successfully',             
            'data': {
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'status': task[3],
                'created_at': task[4],
                'updated_at': task[5]
            }
        }), 201

    except Exception as e:
        print(f"Error: {e}", flush=True)
        logging.error(f"Error: {e}")
        app.logger.info(f"Error: {e}")
        app.logger.exception("An unexpected error occurred")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)

@task_bp.route('/<int:task_id>', methods=['PUT'])
@token_required
def update_task(user_id, task_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        
        # Validate status if provided
        if 'status' in data and data['status'] not in ['pending', 'in_progress', 'completed']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid status. Must be one of: pending, in_progress, completed'
            }), 400

        # Get database connection
        conn = get_db_connection()

        # Check if task exists and belongs to the current user
        cursor = execute_query(conn,
            "SELECT id FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Task not found'
            }), 404

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

        return jsonify({
            'status': 'success',
            'message': 'Task updated successfully',
            'data': {
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'status': task[3],
                'created_at': task[4],
                'updated_at': task[5]
            }
        }), 200

    except Exception as e:
        print(f"Error: {e}", flush=True)
        logging.error(f"Error: {e}")
        app.logger.info(f"Error: {e}")
        app.logger.exception("An unexpected error occurred")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)

@task_bp.route('/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(user_id, task_id):
    conn = None
    cursor = None
    try:
        # Get database connection
        conn = get_db_connection()

        # Check if task exists and belongs to the current user
        cursor = execute_query(conn,
            "SELECT id FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': 'Task not found'
            }), 404

        # Delete task
        cursor = execute_update(conn,
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )

        return jsonify({
            'status': 'success',
            'message': 'Task deleted successfully'
        }), 200

    except Exception as e:
        print(f"Error: {e}", flush=True)
        logging.error(f"Error: {e}")
        app.logger.info(f"Error: {e}")
        app.logger.exception("An unexpected error occurred")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=port)

    