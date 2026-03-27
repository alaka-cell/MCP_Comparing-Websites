from flask import Flask
from flask_cors import CORS
from auth.routes import router as auth_bp
from auth.models import init_db
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey-glam-comparator-2024")

CORS(app, supports_credentials=True, origins=["http://localhost:8501", "http://localhost:3000"])

app.register_blueprint(auth_bp, url_prefix="/auth")

@app.route('/health', methods=['GET'])
def health():
    return {"status": "Flask backend is running on port 8000"}, 200

if __name__ == "__main__":
    # Initialize database on startup
    init_db()
    
    print("Starting Flask backend on http://127.0.0.1:8000")
    app.run(host='127.0.0.1', port=8000, debug=True)