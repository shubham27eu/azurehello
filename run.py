from app import create_app
import os

# Create an app instance
# Load configuration from a config file or environment variables if needed
# e.g., app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
app = create_app()

if __name__ == '__main__':
    # The host needs to be 0.0.0.0 to be accessible from outside the container/sandbox
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
