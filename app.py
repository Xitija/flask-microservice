from flask import Flask
from services.users import user_bp
from services.tasks import task_bp

def create_app():
    app = Flask(__name__)
    
    # Register blueprints with URL prefixes
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(task_bp, url_prefix='/api/tasks')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000) 