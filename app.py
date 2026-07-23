import os
import sys
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from auth.firebase_client import create_user, get_user_profile, update_user_defaults
from auth.session import create_token, verify_token
import jwt

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intelligence.tools.current_aqi import current_aqi
from intelligence.tools.forecast import forecast
from intelligence.tools.trend import trend
from intelligence.tools.health import health
from intelligence.nafasai_agent import ask_nafas

app = Flask(__name__)

CITIES = ["karachi", "lahore", "islamabad"]

# ─────────────────────────────────────────────
# Page
# ─────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("auth.html")

@app.route("/")
def index():
    # Check if user has a valid token — if not redirect to login
    # Token check happens client-side in main.js
    return render_template("index.html")

# ─────────────────────────────────────────────
# Route 1: All three cities current AQI
# ─────────────────────────────────────────────
@app.route("/api/dashboard")
def dashboard():
    results = {}
    for city in CITIES:
        results[city] = current_aqi(city)
    return jsonify(results)

# ─────────────────────────────────────────────
# Route 2: Forecast for one city
# ─────────────────────────────────────────────
@app.route("/api/forecast/<city>")
def get_forecast(city):
    if city.lower() not in CITIES:
        return jsonify({"success": False, "error": "City not supported"})
    return jsonify(forecast(city))

# ─────────────────────────────────────────────
# Route 3: Historical trend for one city
# ─────────────────────────────────────────────
@app.route("/api/trend/<city>")
def get_trend(city):
    if city.lower() not in CITIES:
        return jsonify({"success": False, "error": "City not supported"})
    return jsonify(trend(city))

# ─────────────────────────────────────────────
# Route 4: Chat with NafasAI agent
# ─────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    body     = request.get_json()
    question = body.get("question", "").strip()
    city     = body.get("city", "karachi").lower()
    profile  = body.get("profile", "general").lower()

    if not question:
        return jsonify({"success": False, "error": "No question provided"})

    try:
        
        answer = ask_nafas(question, city, profile)
        
        
        if not answer or answer.strip() == "":
            return jsonify({
                "success": False,
                "error": "NafasAI is temporarily unavailable. Please try again in a moment. string empty"
            })
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "NafasAI is temporarily unavailable. Please try again in a moment. error"
        })

# ── Signup ──
@app.route("/api/signup", methods=["POST"])
def signup():
    body         = request.get_json()
    name         = body.get("name", "").strip()
    email        = body.get("email", "").strip()
    password     = body.get("password", "").strip()
    default_city = body.get("default_city", "karachi")
    health_profile = body.get("health_profile", "general")

    if not all([name, email, password]):
        return jsonify({"success": False, "error": "All fields required"})

    result = create_user(email, password, name, default_city, health_profile)
    if result["success"]:
        token = create_token(result["uid"], email)
        return jsonify({"success": True, "token": token, 
                       "name": name, "default_city": default_city,
                       "health_profile": health_profile})
    return jsonify(result)

# ── Login ──
@app.route("/api/login", methods=["POST"])
def login():
    body     = request.get_json()
    email    = body.get("email", "").strip()
    password = body.get("password", "").strip()

    try:
        from firebase_admin import auth as fb_auth
        # Verify via Firebase REST API
        import requests as req
        api_key = os.getenv("FIREBASE_WEB_API_KEY")
        resp = req.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": email, "password": password, "returnSecureToken": True}
        )
        data = resp.json()
        if "error" in data:
            return jsonify({"success": False, "error": "Invalid email or password"})

        uid     = data["localId"]
        profile = get_user_profile(uid)
        token   = create_token(uid, email)

        return jsonify({
            "success": True,
            "token": token,
            "name": profile["profile"].get("name"),
            "default_city": profile["profile"].get("default_city", "karachi"),
            "health_profile": profile["profile"].get("health_profile", "general")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ── Get profile ──
@app.route("/api/profile", methods=["GET"])
def get_profile():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    verified = verify_token(token)
    if not verified["success"]:
        return jsonify(verified), 401
    return jsonify(get_user_profile(verified["uid"]))

# ── Save defaults ──
@app.route("/api/save-defaults", methods=["POST"])
def save_defaults():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    verified = verify_token(token)
    if not verified["success"]:
        return jsonify(verified), 401
    body = request.get_json()
    return jsonify(update_user_defaults(
        verified["uid"],
        body.get("city", "karachi"),
        body.get("health_profile", "general")
    ))

# ── Logout ──
@app.route("/api/logout", methods=["POST"])
def logout():
    # JWT is stateless — logout handled client-side by deleting token
    return jsonify({"success": True})
        
@app.route("/api/health", methods=["POST"])
def get_health():
    body         = request.get_json()
    pm25         = body.get("pm25", 0)
    forecast_pm25 = body.get("forecast_pm25")
    profile      = body.get("profile", "general")
    return jsonify(health(pm25, forecast_pm25, profile))





if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)