import os
from services.utils.db_utils import get_db_connection

def init_db():
    # Open the connection to SQLite Cloud
    conn = get_db_connection()

    try:
        # Read and execute schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        # Execute the schema SQL
        conn.execute(schema_sql)

        # Verify tables were created
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Created tables:", tables)
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()