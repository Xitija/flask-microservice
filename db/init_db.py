import sqlitecloud
import os

def init_db():
    # Open the connection to SQLite Cloud
    conn = sqlitecloud.connect("sqlitecloud://cvspla7knk.g4.sqlite.cloud:8860/task-management?apikey=VaIaDAUnEARXWoVTXxAQmaRHa5Acnf6I3mb1RIFeR6Q")

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