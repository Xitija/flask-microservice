import sqlitecloud
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def seed_db():
    # Get database credentials from environment variables
    db_url = os.getenv('DB_URL')
    
    if not db_url:
        raise ValueError("Database URL not found in environment variables")

    # Open the connection to SQLite Cloud
    conn = sqlitecloud.connect(db_url)

    try:
        # Sample data for tasks table
        tasks_data = [
            {
                'title': 'Complete project documentation',
                'description': 'Write comprehensive documentation for the project including API endpoints and database schema',
                'status': 'pending'
            },
            {
                'title': 'Review pull requests',
                'description': 'Review and test all pending pull requests for the current sprint',
                'status': 'in-progress'
            },
            {
                'title': 'Fix bug in login system',
                'description': 'Investigate and fix the authentication issue in the login system',
                'status': 'completed'
            },
            {
                'title': 'Implement user profile page',
                'description': 'Create a new page for users to view and edit their profile information',
                'status': 'pending'
            },
            {
                'title': 'Add task filtering',
                'description': 'Implement filtering functionality for tasks based on status and date',
                'status': 'in-progress'
            },
            {
                'title': 'Optimize database queries',
                'description': 'Review and optimize slow database queries to improve application performance',
                'status': 'pending'
            },
            {
                'title': 'Set up CI/CD pipeline',
                'description': 'Configure continuous integration and deployment pipeline for automated testing and deployment',
                'status': 'in-progress'
            },
            {
                'title': 'Implement error logging',
                'description': 'Add comprehensive error logging system to track and debug application issues',
                'status': 'completed'
            },
            {
                'title': 'Create API documentation',
                'description': 'Generate Swagger/OpenAPI documentation for all REST endpoints',
                'status': 'pending'
            },
            {
                'title': 'Add user authentication',
                'description': 'Implement JWT-based authentication system for secure user access',
                'status': 'in-progress'
            },
            {
                'title': 'Design database schema',
                'description': 'Create and optimize database schema for the new feature requirements',
                'status': 'completed'
            },
            {
                'title': 'Implement search functionality',
                'description': 'Add advanced search capabilities with filters and sorting options',
                'status': 'pending'
            },
            {
                'title': 'Update UI components',
                'description': 'Modernize user interface components with new design system',
                'status': 'in-progress'
            },
            {
                'title': 'Add data export feature',
                'description': 'Implement functionality to export task data in various formats (CSV, Excel)',
                'status': 'pending'
            },
            {
                'title': 'Set up monitoring system',
                'description': 'Configure application monitoring and alerting system',
                'status': 'completed'
            }
        ]

        # Insert sample tasks
        for task in tasks_data:
            conn.execute(
                "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
                (task['title'], task['description'], task['status'])
            )

        print("Database seeded successfully with task data!")

    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    seed_db() 