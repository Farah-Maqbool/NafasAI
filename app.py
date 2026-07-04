import os
import sys
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

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
        print(f"CHAT: question={question} city={city} profile={profile}")
        answer = ask_nafas(question, city, profile)
        print(f"CHAT: answer length={len(answer) if answer else 0}")
        print(f"CHAT: answer preview={answer[:200] if answer else 'EMPTY'}")
        
        if not answer or answer.strip() == "":
            return jsonify({
                "success": False,
                "error": "NafasAI is temporarily unavailable. Please try again in a moment. string empty"
            })
        return jsonify({"success": True, "answer": answer})
    except Exception as e:
        print(f"CHAT ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "NafasAI is temporarily unavailable. Please try again in a moment. error"
        })
        
@app.route("/api/health", methods=["POST"])
def get_health():
    body         = request.get_json()
    pm25         = body.get("pm25", 0)
    forecast_pm25 = body.get("forecast_pm25")
    profile      = body.get("profile", "general")
    return jsonify(health(pm25, forecast_pm25, profile))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)