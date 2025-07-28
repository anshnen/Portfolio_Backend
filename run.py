import os
from app import create_app

config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    with app.app_context():
        print("Starting application...")
        app.run(host='0.0.0.0', port=5000)        
        print("Application started successfully.")