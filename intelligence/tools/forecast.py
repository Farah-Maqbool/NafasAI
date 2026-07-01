import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

city_models   = joblib.load(os.path.join(BASE_DIR, "modeling/city_models.pkl"))
feature_names = joblib.load(os.path.join(BASE_DIR, "modeling/feature_names.pkl"))


import numpy as np
import pandas as pd
from datetime import datetime, timezone

from intelligence.tools.current_aqi import current_aqi





def get_pm25_category(pm25: float) -> str:
    if pm25 <= 12:
        return "Good"

    if pm25 <= 35:
        return "Moderate"

    if pm25 <= 55:
        return "Unhealthy for Sensitive Groups"

    if pm25 <= 150:
        return "Unhealthy"

    return "Hazardous"


def forecast(city: str) -> dict:
    """
    Predict PM2.5 concentration 24 hours ahead.

    Returns:
    {
        city,
        current_pm25,
        predicted_pm25,
        category
    }
    """

    live = current_aqi(city)

    if not live["success"]:
        return live

    readings = live["recent_pm25"]
    current_pm25 = live["pm25"]

    now = datetime.now(timezone.utc)

    features = {

        "hour_of_day": now.hour,

        "day_of_week": now.weekday(),

        "month": now.month,

        "is_weekend": int(now.weekday() >= 5),

        "pm25_lag_1": readings[-1],

        "pm25_lag_3": readings[-3] if len(readings) >= 3 else current_pm25,

        "pm25_lag_6": readings[-6] if len(readings) >= 6 else current_pm25,

        "pm25_lag_12": readings[-12] if len(readings) >= 12 else current_pm25,

        "pm25_lag_18": readings[-18] if len(readings) >= 18 else current_pm25,

        "pm25_lag_24": readings[-24] if len(readings) >= 24 else current_pm25,

        "pm25_lag_48": readings[-48] if len(readings) >= 48 else current_pm25,

        "pm25_rolling_6h": np.mean(readings[-6:]),

        "pm25_rolling_24h": np.mean(readings[-24:]),

        "ozone": live["ozone"] or 50,

        "dust": live["dust"] or 40,

        "carbon_monoxide": live["carbon_monoxide"] or 180,

        "nitrogen_dioxide": live["nitrogen_dioxide"] or 5,

        "sulphur_dioxide": live["sulphur_dioxide"] or 5,
    }

    X = pd.DataFrame([features])[feature_names]

    model = city_models[city.lower()]

    prediction = float(model.predict(X)[0])

    return {

        "success": True,

        "city": city.title(),

        "current_pm25": round(current_pm25, 1),

        "predicted_pm25_24h": round(prediction, 1),

        "forecast_category": get_pm25_category(prediction),
    }