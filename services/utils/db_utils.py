import os
import sqlitecloud
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables from the correct path
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env', '.env'))

@contextmanager
def get_db_connection():
    """Create and return a database connection with context management"""
    db_url = os.getenv('DB_URL')
    print(f"DB URL: {db_url}")
    if not db_url:
        raise ValueError("Database URL not found in environment variables")
    
    conn = None
    try:
        conn = sqlitecloud.connect(db_url)
        yield conn
    except Exception as e:
       return jsonify({
          'status': 'error',
          'message': str(e)
        }), 500

def execute_query(query, params=None, fetch_one=False):
    """Execute a query and return results"""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params or ())
        if fetch_one:
            return cursor.fetchone()
        return cursor.fetchall()

def execute_update(query, params=None):
    """Execute an update query and commit changes"""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params or ())
        conn.commit()
        return cursor 