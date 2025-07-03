from flask import Flask
from routes import api_bp # Import the blueprint

app = Flask(__name__)

# Register the blueprint
app.register_blueprint(api_bp)

@app.route('/')
def hello_world():
    return 'Hello, World! Visit /api/health for API health check.'

if __name__ == '__main__':
    app.run(debug=True)
