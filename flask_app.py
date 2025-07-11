from flask import Flask
from flask_cors import CORS
from auth.routes import router as auth_bp

app = Flask(__name__)
app.secret_key = "supersecretkey" 
CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp, url_prefix="/auth")

if __name__ == "__main__":
    app.run(port=5000)
