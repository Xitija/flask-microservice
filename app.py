from flask import Flask
from services.users import user_bp
from services.tasks import task_bp

def create_app():
    app = Flask(__name__)
    print("Initializing Flask app...", flush=True)
    # Register blueprints with URL prefixes
    # app.register_blueprint(user_bp, url_prefix='/api/users')
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