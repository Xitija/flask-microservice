import os
import sys
from datetime import datetime

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from services.utils.db_utils import get_db_connection, execute_query, execute_update, close_cursor, close_connection
from services.utils.auth_utils import hash_password

def migrate_tasks():
    conn = None
    cursor = None
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create users table if it doesn't exist
        cursor = execute_update(conn,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        print("Created users table if it didn't exist")
        
        # Create tasks table if it doesn't exist
        cursor = execute_update(conn,
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        print("Created tasks table if it didn't exist")
        
        # Check if tasks table has all required columns
        cursor = execute_query(conn,
            "PRAGMA table_info(tasks)"
        )
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Add missing columns if they don't exist
        if 'created_at' not in columns:
            cursor = execute_update(conn,
                "ALTER TABLE tasks ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
            print("Added created_at column")
            
        if 'updated_at' not in columns:
            cursor = execute_update(conn,
                "ALTER TABLE tasks ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
            print("Added updated_at column")
            
        if 'user_id' not in columns:
            cursor = execute_update(conn,
                "ALTER TABLE tasks ADD COLUMN user_id INTEGER"
            )
            print("Added user_id column")
            
        if 'status' not in columns:
            cursor = execute_update(conn,
                "ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'"
            )
            print("Added status column")
        
        # Create a default admin user if it doesn't exist
        cursor = execute_query(conn,
            "SELECT id FROM users WHERE username = 'admin'"
        )
        admin_user = cursor.fetchone()
        
        if not admin_user:
            # Create default admin user
            hashed_password = hash_password('admin123')
            cursor = execute_update(conn,
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                RETURNING id
                """,
                ('admin', hashed_password)
            )
            admin_id = cursor.fetchone()[0]
            print("Created default admin user")
        else:
            admin_id = admin_user[0]
            print("Using existing admin user")
        
        # Get current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update existing tasks to be associated with the admin user and set timestamps
        cursor = execute_update(conn,
            """
            UPDATE tasks 
            SET user_id = ?, 
                updated_at = ?,
                created_at = COALESCE(created_at, ?),
                status = COALESCE(status, 'pending')
            WHERE user_id IS NULL
            """,
            (admin_id, current_time, current_time)
        )
        
        # Verify the migration
        cursor = execute_query(conn,
            "SELECT COUNT(*) FROM tasks WHERE user_id IS NULL"
        )
        remaining_null_user_id = cursor.fetchone()[0]
        
        cursor = execute_query(conn,
            "SELECT COUNT(*) FROM tasks WHERE created_at IS NULL OR updated_at IS NULL"
        )
        remaining_null_timestamps = cursor.fetchone()[0]
        
        print(f"Migration completed:")
        print(f"- Tasks associated with admin user: {admin_id}")
        print(f"- Remaining tasks with NULL user_id: {remaining_null_user_id}")
        print(f"- Remaining tasks with NULL timestamps: {remaining_null_timestamps}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if cursor:
            close_cursor(cursor)
        if conn:
            close_connection(conn)

if __name__ == '__main__':
    migrate_tasks() 