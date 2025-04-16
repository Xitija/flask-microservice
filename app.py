from flask import Flask
from flask_restx import Api
from services.users import user_bp, init_app as init_users
from services.tasks import task_bp, init_app as init_tasks

def create_app():
    app = Flask(__name__)
    print("Initializing Flask app...", flush=True)
    
    # Create a single API instance
    api = Api(
        app,
        version='1.0',
        title='Task Management API',
        description='A simple task management API with user authentication',
        doc='/swagger'
    )
    
    # Initialize both services with the same API instance
    init_users(api)
    init_tasks(api)
    
    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(task_bp)
    
    print("\nRegistered URL routes:", flush=True)
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule}", flush=True)
    
    # Enable CORS for all routes
    # @app.after_request
    # def after_request(response):
    #     response.headers.add('Access-Control-Allow-Origin', '*')
    #     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    #     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    #     return response
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000) 