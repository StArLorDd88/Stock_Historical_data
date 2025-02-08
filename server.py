from flask import Flask, request, redirect, session, jsonify
import requests

app = Flask(__name__)
app.secret_key = "2356"  # Change this for security

# Replace with your Upstox API credentials
API_KEY = "3146de73-0e14-4bac-af8c-b248c718e43e"
API_SECRET = "tpfd7qwdmd"
REDIRECT_URI = "http://127.0.0.1:5000/callback"

# Upstox API Endpoints
AUTH_URL = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}&state=xyz"
TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
PROFILE_URL = "https://api.upstox.com/v2/user/profile"


@app.route('/')
def login():
    """Redirects the user to the Upstox login page."""
    return redirect(AUTH_URL)


@app.route('/callback')
def callback():
    """Handles the OAuth callback and retrieves an access token."""
    code = request.args.get("code")

    if not code:
        return "Authorization failed", 400

    payload = {
        "code": code,
        "client_id": API_KEY,
        "client_secret": API_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(TOKEN_URL, data=payload)

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return "Failed to decode response from Upstox", 500

    if "access_token" not in data:
        return jsonify({"error": data}), 400

    session["access_token"] = data["access_token"]
    return redirect("/profile")


@app.route('/profile')
def profile():
    # Fetches the user's profile from Upstox
    if "access_token" not in session:
        return redirect("/")

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.get(PROFILE_URL, headers=headers)

    try:
        profile_data = response.json()
    except requests.exceptions.JSONDecodeError:
        return "Failed to decode profile response", 500

    return jsonify(profile_data)


@app.route('/historical-candle', methods=['GET'])
def historical_candle():
    # Fetches historical candle data for a given instrument
    if "access_token" not in session:
        return jsonify({"error": "Unauthorized, please login first"}), 401

    # Get query parameters
    instrument_key = request.args.get("instrument_key")
    interval = request.args.get("interval", "1minute")  # Default interval to 1 minute
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # Validate parameters
    if not instrument_key or not from_date or not to_date:
        return jsonify({"error": "Missing required parameters (instrument_key, from_date, to_date)"}), 400

    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {session['access_token']}",
    }

    response = requests.get(url, headers=headers)

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        return jsonify({"error": "Failed to decode response from Upstox"}), 500

    return jsonify(data)
