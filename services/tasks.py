import datetime
import os
import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from utils.db_utils import get_db_connection

# Load environment variables from the correct path
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env', '.env'))

app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))
print(f"Port: {port}")
@app.route("/")
def home():
    return "Hello, this is a Flask Microservice" + " "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@app.route("/api/tasks", methods=["GET", "POST"])
def handle_tasks():
    if request.method == "GET":
        return get_tasks()
    elif request.method == "POST":
        return create_task()

def get_tasks():
    conn = None
    try:
        # Get pagination parameters from query string
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid pagination parameters: page and per_page must be integers'
            }), 400
        
        # Validate pagination parameters
        if page < 1 or per_page < 1:
            return jsonify({
                'status': 'error',
                'message': 'Invalid pagination parameters: page and per_page must be positive integers'
            }), 400
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get database connection
        try:
            conn = get_db_connection()
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
        
        # Get total count of tasks
        cursor = conn.execute("SELECT COUNT(*) FROM tasks")
        total = cursor.fetchone()[0]
        
        # Get paginated tasks
        cursor = conn.execute(
            "SELECT * FROM tasks LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        tasks = cursor.fetchall()
        
        # Convert tasks to list of dictionaries
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'status': task[3]
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
        app.logger.exception("An unexpected error occurred")  # logs traceback too
        return jsonify({
            'error': e,
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                app.logger.info(f"Error closing database connection: {e}")
                # We don't return anything here since we're in a finally block
                # and the response has already been sent

def create_task():
    conn = None
    try:
        # Validate required fields
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        required_fields = ['title', 'description']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Validate field types and lengths
        if not isinstance(data['title'], str) or len(data['title'].strip()) == 0:
            return jsonify({
                'status': 'error',
                'message': 'Title must be a non-empty string'
            }), 400

        if not isinstance(data['description'], str):
            return jsonify({
                'status': 'error',
                'message': 'Description must be a string'
            }), 400

        # Get database connection
        try:
            conn = get_db_connection()
        except ValueError as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

        # Insert new task and get the created task in one query
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, status) 
            VALUES (?, ?, ?)
            RETURNING id, title, description, status
            """,
            (data['title'].strip(), data['description'], 'pending')
        )
        conn.commit()
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
        if conn:
            try:
                conn.close()
            except Exception as e:
                app.logger.info(f"Error closing database connection: {e}")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)

    