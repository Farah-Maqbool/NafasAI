import requests
import pandas as pd
from datetime import datetime, timezone
from google.cloud import bigquery
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
TABLE_ID = f"{PROJECT_ID}.air_quality.karachi_readings"

CITIES = {
    "karachi" : {"lat":24.86, "lon":67.01},
    "lahore" : {"lat":31.55,"lon":74.35},
    "islamabad" : {"lat":33.72,"lon":73.06}
}

def calculate_aqi(pm25):
    """Simple AQI calculation from PM2.5 (EPA Breakpoints)"""
    if pm25 is None:
        return None
    
    if pm25 <= 12.0:   return int((50/12.0) * pm25)
    if pm25 <= 35.4:   return int(50 + (50/23.4) * (pm25 - 12.0))
    if pm25 <= 55.4:   return int(100 + (50/20.0) * (pm25 - 35.4))
    if pm25 <= 150.4:  return int(150 + (50/94.9) * (pm25 - 55.4))
    if pm25 <= 250.4:  return int(200 + (100/99.9) * (pm25 - 150.4))
    return 300

def fetch_current_air_quality(city_name):
    coords = CITIES[city_name]
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={coords['lat']}&longitude={coords['lon']}"
        f"&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
        f"sulphur_dioxide,ozone,dust,uv_index"
    )
    response = requests.get(url)
    data = response.json()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    times = data["hourly"]["time"]

    if now in times:
        idx = times.index(now)
    else:
        idx = 0 

    h = data["hourly"]
    pm25_val = h["pm2_5"][idx]

    record = {
        "city": city_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pm25": pm25_val,
        "pm10": h["pm10"][idx],
        "carbon_monoxide": h["carbon_monoxide"][idx],
        "nitrogen_dioxide": h["nitrogen_dioxide"][idx],
        "sulphur_dioxide": h["sulphur_dioxide"][idx],
        "ozone": h["ozone"][idx],
        "dust": h["dust"][idx],
        "uv_index": h["uv_index"][idx],
        "aqi_calculated": calculate_aqi(pm25_val),
    }
    return record

def push_to_bigquery(record):
    client = bigquery.Client(project=PROJECT_ID)
    errors = client.insert_rows_json(TABLE_ID, [record])
    if errors:
        print("Insert errors:", errors)
    else:
        print("Inserted successfully:", record)

if __name__ == "__main__":
    for city in CITIES:
        print(f"\nFetching {city}...")
        record = fetch_current_air_quality(city)
        print("Fetched:", record)
        push_to_bigquery(record)
