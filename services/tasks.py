import datetime
import os
import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from utils.db_utils import get_db_connection, execute_query, execute_update, close_cursor, close_connection

# Load environment variables from the correct path
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env', '.env'))

app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))
print(f"Port: {port}")

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

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        error_response = validate_task_data(data)
        if error_response:
            return error_response

        # Get database connection
        conn = get_db_connection()

        # Check if task exists
        cursor = execute_query(conn, "SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': f'Task with id {task_id} not found'
            }), 404

        # Prepare update query
        update_fields = []
        update_values = []
        for field in data.keys():
            if field == 'title':
                update_fields.append('title = ?')
                update_values.append(data['title'].strip())
            else:
                update_fields.append(f'{field} = ?')
                update_values.append(data[field])

        # Add task_id to values
        update_values.append(task_id)

        # Execute update
        update_query = f"""
            UPDATE tasks 
            SET {', '.join(update_fields)}
            WHERE id = ?
            RETURNING id, title, description, status
        """
        cursor = execute_update(conn, update_query, update_values)
        updated_task = cursor.fetchone()

        return jsonify({
            'status': 'success',
            'message': 'Task updated successfully',
            'data': {
                'id': updated_task[0],
                'title': updated_task[1],
                'description': updated_task[2],
                'status': updated_task[3]
            }
        }), 200

    except Exception as e:
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

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = None
    cursor = None
    try:
        # Get database connection
        conn = get_db_connection()

        # Check if task exists
        cursor = execute_query(conn, "SELECT * FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            return jsonify({
                'status': 'error',
                'message': f'Task with id {task_id} not found'
            }), 404

        # Delete the task
        cursor = execute_update(conn, "DELETE FROM tasks WHERE id = ?", (task_id,))

        response = jsonify({
            'status': 'success',
            'message': f'Task with id {task_id} deleted successfully'
        }), 200
        return response

    except Exception as e:
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

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    conn = None
    cursor = None
    try:
        # Get pagination parameters
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid pagination parameters: page and per_page must be integers'
            }), 400

        if page < 1 or per_page < 1:
            return jsonify({
                'status': 'error',
                'message': 'Invalid pagination parameters: page and per_page must be positive integers'
            }), 400

        # Calculate offset
        offset = (page - 1) * per_page

        # Get database connection
        conn = get_db_connection()

        # Get total count and tasks
        cursor = execute_query(conn, "SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]

        cursor = execute_query(conn, "SELECT * FROM tasks LIMIT ? OFFSET ?", (per_page, offset))
        tasks = cursor.fetchall()

        # Convert tasks to list of dictionaries
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task[0],
                'title': task[2],
                'description': task[3],
                'status': task[4]
            })
        
        # Calculate total pages floor division
        total_pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'status': 'success',
            'data': task_list,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }), 200

    except Exception as e:
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

@app.route("/api/tasks", methods=["POST"])
def create_task():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        error_response = validate_task_data(data, required_fields=['title', 'description'])
        if error_response:
            return error_response

        # Get database connection
        conn = get_db_connection()

        # Insert new task
        cursor = execute_update(
            conn,
            """
            INSERT INTO tasks (title, description, status) 
            VALUES (?, ?, ?)
            RETURNING id, title, description, status
            """,
            (data['title'].strip(), data['description'], 'pending')
        )
        task = cursor.fetchone()

        return jsonify({
            'status': 'success',
            'message': 'Task created successfully',
            'data': {
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'status': task[3]
            }
        }), 201

    except Exception as e:
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

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)

    