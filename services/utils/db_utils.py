import os
import sqlitecloud
from dotenv import load_dotenv
# Load environment variables from the correct path
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env', '.env'))

def get_db_connection():
    """Create and return a database connection"""
    db_url = os.getenv('DB_URL')
    if not db_url:
        raise ValueError("Database URL not found in environment variables")
    return sqlitecloud.connect(db_url)

def execute_query(conn, query, params=None):
    """Execute a query and return cursor"""
    return conn.execute(query, params or ())

def execute_update(conn, query, params=None):
    """Execute an update query and return cursor"""
    cursor = conn.execute(query, params or ())
    conn.commit()
    return cursor

def close_cursor(cursor):
    """Close the cursor"""
    if cursor:
        cursor.close()

def close_connection(conn):
    """Close the database connection"""
    if conn:
        conn.close() 