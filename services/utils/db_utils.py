import os
import sqlitecloud
from dotenv import load_dotenv

# Load environment variables from the correct path
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env', '.env'))

def get_db_connection():
    """Create and return a database connection"""
    db_url = os.getenv('DB_URL')
    print(f"DB URL: {db_url}")
    if not db_url:
        raise ValueError("Database URL not found in environment variables")
    return sqlitecloud.connect(db_url) 