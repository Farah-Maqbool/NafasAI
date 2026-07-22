import os

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")

TABLE_NAME = f"{PROJECT_ID}.air_quality.karachi_readings"

client = bigquery.Client(project=PROJECT_ID)


def trend(city: str) -> dict:
    """
    Retrieve historical PM2.5 statistics for up to the last 7 days.

    If fewer than 7 days of data are available, the statistics are
    calculated using the available data. If no data exists, a
    friendly response is returned.
    """

    print(f"DEBUG trend called with city: '{city}'")

    query = f"""
    WITH latest AS (
        SELECT MAX(timestamp) AS latest_timestamp
        FROM `{TABLE_NAME}`
    )

    SELECT
        ROUND(AVG(pm25), 1) AS average_pm25,
        ROUND(MIN(pm25), 1) AS minimum_pm25,
        ROUND(MAX(pm25), 1) AS maximum_pm25,
        COUNT(*) AS total_readings,
        COUNT(DISTINCT DATE(timestamp)) AS days_available
    FROM `{TABLE_NAME}`, latest
    WHERE LOWER(city) = LOWER(@city)
    AND timestamp >= TIMESTAMP_SUB(latest_timestamp, INTERVAL 7 DAY)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "city",
                "STRING",
                city
            )
        ]
    )


    try:

        rows = list(
            client.query(
                query,
                job_config=job_config
            ).result()
        )
        print(f"DEBUG rows returned: {len(rows)}")

        if rows:
            print(f"DEBUG row data: {dict(rows[0])}")
        if not rows:
            return {
                "success": False,
                "error": "Unable to retrieve historical data."
            }

        row = rows[0]

        # No historical data available
        if row.total_readings == 0:

            return {

                "success": True,

                "city": city.title(),

                "days_available": 0,

                "average_pm25": None,

                "minimum_pm25": None,

                "maximum_pm25": None,

                "total_readings": 0,

                "message": "No historical air quality data is available yet."
            }

        # Return whatever history exists (1–7 days)

        return {

            "success": True,

            "city": city.title(),

            "days_available": row.days_available,

            "average_pm25": row.average_pm25,

            "minimum_pm25": row.minimum_pm25,

            "maximum_pm25": row.maximum_pm25,

            "total_readings": row.total_readings,

            "message": (
                f"Statistics are based on "
                f"{row.days_available} day(s) of available historical data."
            )
        }

    except Exception as e:

        return {

            "success": False,

            "error": str(e)
        }