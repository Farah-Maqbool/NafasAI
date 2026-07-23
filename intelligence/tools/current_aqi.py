import requests
from datetime import datetime, timezone

SUPPORTED_CITIES = {
    "karachi":    {"latitude": 24.86, "longitude": 67.01},
    "lahore":     {"latitude": 31.55, "longitude": 74.35},
    "islamabad":  {"latitude": 33.72, "longitude": 73.06},
    "peshawar":   {"latitude": 34.01, "longitude": 71.57},
    "quetta":     {"latitude": 30.18, "longitude": 67.00},
    "faisalabad": {"latitude": 31.42, "longitude": 73.08},
    "multan":     {"latitude": 30.19, "longitude": 71.47},
}


def get_pm25_category(pm25: float) -> str:
    """Convert PM2.5 concentration into an air quality category."""

    if pm25 <= 12:
        return "Good"

    if pm25 <= 35:
        return "Moderate"

    if pm25 <= 55:
        return "Unhealthy for Sensitive Groups"

    if pm25 <= 150:
        return "Unhealthy"

    return "Hazardous"


def current_aqi(city: str) -> dict:
    """
    Fetch the latest live air quality information from Open-Meteo.

    Returns:
        {
            city,
            pm25,
            pm10,
            ozone,
            carbon_monoxide,
            nitrogen_dioxide,
            sulphur_dioxide,
            dust,
            category,
            timestamp
        }
    """

    city = city.lower().strip()

    if city not in SUPPORTED_CITIES:
        return {
            "success": False,
            "error": f"{city} is not currently supported."
        }

    coordinates = SUPPORTED_CITIES[city]

    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={coordinates['latitude']}"
        f"&longitude={coordinates['longitude']}"
        "&hourly="
        "pm2_5,"
        "pm10,"
        "ozone,"
        "carbon_monoxide,"
        "nitrogen_dioxide,"
        "sulphur_dioxide,"
        "dust"
        "&past_days=3"
    )

    try:

        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()

        hourly = data.get("hourly")

        if hourly is None:
            return {
                "success": False,
                "error": "Unable to retrieve air quality data."
            }

        timestamps = hourly["time"]
        pm25_values = hourly["pm2_5"]

        current_hour = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:00")

        if current_hour in timestamps:
            index = timestamps.index(current_hour)

        else:
            index = next(
                (
                    i
                    for i in range(len(pm25_values) - 1, -1, -1)
                    if pm25_values[i] is not None
                ),
                -1,
            )

        if index == -1:
            return {
                "success": False,
                "error": "No valid PM2.5 reading found."
            }

        pm25 = hourly["pm2_5"][index] or 0

        return {

            "success": True,

            "city": city.title(),

            "pm25": round(pm25, 1),

            "pm10": hourly["pm10"][index],

            "ozone": hourly["ozone"][index],

            "carbon_monoxide": hourly["carbon_monoxide"][index],

            "nitrogen_dioxide": hourly["nitrogen_dioxide"][index],

            "sulphur_dioxide": hourly["sulphur_dioxide"][index],

            "dust": hourly["dust"][index],

            "category": get_pm25_category(pm25),

            "timestamp": timestamps[index],

            "recent_pm25": [
                value
                for value in pm25_values[: index + 1]
                if value is not None
            ][-48:],
        }

    except requests.RequestException as e:

        return {
            "success": False,
            "error": str(e),
        }