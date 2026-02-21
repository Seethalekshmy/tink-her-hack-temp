# routes/auth_routes.py — Handles Gmail OAuth 2.0 login flow
# OAuth 2.0 is like "Login with Google" but for accessing Gmail data

from flask import Blueprint, redirect, session, request, jsonify
from gmail_service import get_auth_flow, save_credentials

# A Blueprint is like a mini-app — groups related routes together
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth")
def auth():
    """
    STEP 1 of OAuth: Send the user to Google's login page.
    
    When someone visits /auth, we:
    1. Build a special Google login URL
    2. Redirect the user there
    3. Google asks them to approve access to Gmail
    """
    flow = get_auth_flow()

    # Generate the URL that sends users to Google's consent screen
    # access_type="offline" means we get a refresh token (so we don't need to re-login every hour)
    # include_granted_scopes="true" lets us add more permissions later without breaking existing ones
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )

    # Save the "state" token in the session — used to verify the callback isn't fake (CSRF protection)
    session["oauth_state"] = state

    # Send user to Google's login page
    return redirect(auth_url)


@auth_bp.route("/callback")
def callback():
    """
    STEP 2 of OAuth: Google redirects back here after the user approves.
    
    Google sends us a temporary "code" in the URL.
    We exchange that code for real access tokens.
    """
    # Verify the state matches what we stored — prevents CSRF attacks
    if request.args.get("state") != session.get("oauth_state"):
        return jsonify({"error": "State mismatch. Possible CSRF attack."}), 400

    flow = get_auth_flow()

    # Exchange the temporary code Google gave us for real access tokens
    # This is like trading a ticket stub for the actual item
    flow.fetch_token(authorization_response=request.url)

    # Save the credentials (tokens) so we can use them on future requests
    credentials = flow.credentials
    save_credentials(credentials)

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>GREENBYTE — Connected!</title>
      <meta http-equiv="refresh" content="2;url=http://localhost:5500/index.html" />
      <style>
        body {
          font-family: 'Inter', sans-serif;
          background: #0a1a0d;
          color: #4ade80;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          margin: 0;
          font-size: 1.2rem;
        }
        p { color: rgba(240,253,244,0.6); font-size: 0.9rem; margin-top: 12px; }
      </style>
    </head>
    <body>
      <div>✅ Gmail connected successfully!</div>
      <p>Redirecting you back to the dashboard…</p>
      <script>
        setTimeout(() => {
          // Try common local server URLs; adjust if yours differs
          const candidates = [
            'http://localhost:5501/index.html',
            'http://127.0.0.1:5501/index.html'
          ];
          window.location.href = candidates[0];
        }, 2000);
      </script>
    </body>
    </html>
    """
