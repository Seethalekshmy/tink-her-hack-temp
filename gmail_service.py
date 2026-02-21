# services/gmail_service.py — Handles all Gmail API connection logic
# Think of this as the "connector" between our app and Google's servers

import os
import json
from google_auth_oauthlib.flow import Flow         # Manages the OAuth login steps
from google.oauth2.credentials import Credentials  # Represents a logged-in user's tokens
from google.auth.transport.requests import Request # Used to refresh expired tokens
from googleapiclient.discovery import build        # Builds the Gmail API client

# --- Constants ---

# The path to the credentials.json file you downloaded from Google Cloud Console
# This file identifies YOUR app (not the user) to Google
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

# Where we temporarily store the user's access tokens after they log in
# In production, store these in a database per user — NOT a local file
TOKEN_FILE = os.getenv("TOKEN_FILE", "token.json")

# The "scope" defines what permissions we're requesting from the user
# gmail.readonly = read emails but NOT send, delete, or modify
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Your app's redirect URI — must match what you set in Google Cloud Console exactly
# When running locally, this is http://localhost:5001/callback
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5001/callback")


def get_auth_flow():
    """
    Creates a Google OAuth Flow object.
    
    The Flow object manages the entire OAuth handshake process.
    It reads your app's client ID and secret from credentials.json.
    """
    # os.environ is set to allow HTTP (not just HTTPS) for local development
    # NEVER do this in production — remove this line when deploying
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,       # Your downloaded credentials.json
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    return flow


def save_credentials(credentials):
    """
    Saves the user's OAuth tokens to a local file so they stay logged in.
    
    The token contains:
    - access_token: Used to make API calls (expires in ~1 hour)
    - refresh_token: Used to get a new access_token without re-logging in
    """
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else []
    }
    # Write tokens to a JSON file
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)


def get_gmail_service():
    """
    Returns an authenticated Gmail API service client.
    
    Checks if we have saved tokens. If the token is expired, it auto-refreshes it.
    If no token exists at all, it tells the user to authenticate.
    
    Returns: (service, error) — one of them will be None
    """
    # Check if we have saved credentials
    if not os.path.exists(TOKEN_FILE):
        return None, "Not authenticated. Please visit /auth to connect Gmail."

    # Load the saved credentials from file
    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data["token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data["token_uri"],
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data.get("scopes", SCOPES)
    )

    # If the access token has expired, use the refresh token to get a new one
    # This happens automatically every ~1 hour — the user doesn't need to re-login
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                save_credentials(creds)  # Save the new token
            except Exception as e:
                return None, f"Token refresh failed: {str(e)}. Please re-authenticate at /auth."
        else:
            return None, "Invalid credentials. Please re-authenticate at /auth."

    # Build the Gmail API service client
    # "gmail" = which API, "v1" = which version
    try:
        service = build("gmail", "v1", credentials=creds)
        return service, None
    except Exception as e:
        return None, f"Failed to build Gmail service: {str(e)}"
