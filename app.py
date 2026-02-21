# app.py — The main entry point for the GREENBYTE Flask backend
# This file creates the Flask app and registers all the routes

from flask import Flask
from flask_cors import CORS          # Allows your frontend to talk to this backend
from dotenv import load_dotenv       # Loads secrets from .env file
import os

# Load environment variables from .env file BEFORE anything else
load_dotenv()

# Import the route blueprints (each file handles a group of endpoints)
from auth_routes import auth_bp
from email_routes import email_bp

# --- Create the Flask app ---
app = Flask(__name__)

# SECRET_KEY is used by Flask to sign session cookies (keeps login state)
# NEVER hardcode this — always pull from .env
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-for-dev-only")

# --- Enable CORS ---
# Explicit origins required when supports_credentials=True —
# browsers REJECT wildcard "*" for credentialed cross-origin requests.
# Add any other origin you use (e.g. a Vite dev server on port 5173).
CORS(app, supports_credentials=True, origins=[
    "https://tink-her-hack-temp-w295.onrender.com",
    "https://seethalekshmy.github.io"
])

# --- Register Blueprints (route groups) ---
app.register_blueprint(auth_bp)     # Handles /auth and /callback
app.register_blueprint(email_bp)    # Handles /emails/summary

# --- Run the server ---
if __name__ == "__main__":
    # debug=True auto-reloads when you save files — great for development!
    # Set debug=False in production
    app.run(debug=False, host="0.0.0.0", port=10000)
