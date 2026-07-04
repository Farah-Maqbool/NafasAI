import os
from google import genai

from intelligence.tools.current_aqi import current_aqi
from intelligence.tools.forecast import forecast
from intelligence.tools.trend import trend
from intelligence.tools.health import health

from google.adk.agents import Agent
from intelligence.nafasai_prompt import AGENT_PROMPT

nafasai_agent = Agent(
    name="NafasAI_Agent",
    model="gemini-2.5-flash",
    instruction=AGENT_PROMPT,
    description="An intelligent air quality assistant for Pakistan.",
    tools=[current_aqi, forecast, trend, health],
)

def ask_nafas(question: str, city: str = "karachi", profile: str = "general") -> str:
    """
    Orchestrates ADK tools then uses Gemini to compose a grounded answer.
    Uses ADK tool functions directly — same logic the ADK runner would execute.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    client  = genai.Client(api_key=api_key)

    # Call ADK tools
    current = current_aqi(city)
    fc      = forecast(city)
    tr      = trend(city)
    hr      = health(current.get("pm25", 0), fc.get("predicted_pm25_24h"), profile)

    trend_text = (
        f"7-day average: {tr.get('average_pm25')} μg/m³, "
        f"max: {tr.get('maximum_pm25')} μg/m³, "
        f"min: {tr.get('minimum_pm25')} μg/m³"
        if tr.get("total_readings", 0) > 0
        else "Historical trend data is still accumulating."
    )

    prompt = f"""
You are NafasAI — a friendly air quality assistant for Pakistan.
Answer in the same language the user used (English or Roman Urdu).
Be direct and human. Keep answer under 4 sentences unless more detail is needed.
Never make up numbers — only use the data provided below.

LIVE AIR QUALITY — {city.title()}:
- PM2.5: {current.get('pm25')} μg/m³
- Category: {current.get('category')}
- PM10: {current.get('pm10')} μg/m³

24-HOUR FORECAST:
- Predicted PM2.5: {fc.get('predicted_pm25_24h')} μg/m³
- Category: {fc.get('forecast_category')}

7-DAY HISTORICAL TREND:
- {trend_text}

HEALTH ADVICE for profile '{profile}':
- Mask: {hr.get('mask_recommendation')}
- {' '.join(hr.get('precautions', []))}

User question: {question}
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text