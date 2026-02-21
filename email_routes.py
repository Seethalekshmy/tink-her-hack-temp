# routes/email_routes.py — Handles the /emails/summary endpoint
# This is the main endpoint that returns email analysis + carbon footprint data

from flask import Blueprint, jsonify
from gmail_service import get_gmail_service
from email_analyzer import analyze_emails
from carbon_calculator import calculate_carbon

email_bp = Blueprint("email", __name__)


@email_bp.route("/emails/summary")
def email_summary():
    """
    GET /emails/summary
    
    Returns a JSON object with:
    - Email statistics (count, size, old emails, large attachments)
    - Carbon footprint estimate
    
    Requires the user to have completed /auth first.
    """
    # Get an authenticated Gmail API client
    # If not authenticated, this will return an error
    service, error = get_gmail_service()
    if error:
        return jsonify({
            "error": error,
            "hint": "Visit /auth first to connect your Gmail account"
        }), 401

    # Fetch and analyze email metadata from Gmail
    # We only read metadata (size, date, labels) — NOT the email content/body
    analysis, error = analyze_emails(service)
    if error:
        return jsonify({"error": error}), 500

    # Calculate carbon footprint from the storage data
    carbon_data = calculate_carbon(analysis["total_size_mb"])

    # Return everything as a clean JSON response
    return jsonify({
        "status": "success",
        "email_stats": analysis,
        "carbon_footprint": carbon_data,
        "message": "💚 GREENBYTE analysis complete"
    })
