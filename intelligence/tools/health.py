from typing import Optional


def _get_pm25_category(pm25: float) -> str:
    """Convert PM2.5 concentration into an air quality category."""

    if pm25 <= 12:
        return "Good"
    elif pm25 <= 35:
        return "Moderate"
    elif pm25 <= 55:
        return "Unhealthy for Sensitive Groups"
    elif pm25 <= 150:
        return "Unhealthy"

    return "Hazardous"


def health(
    current_pm25: float,
    forecast_pm25: Optional[float] = None,
    user_profile: str = "general",
) -> dict:
    """
    Generate health recommendations based on current and optionally
    forecasted PM2.5 values.

    Parameters
    ----------
    current_pm25 : float
        Current PM2.5 concentration.

    forecast_pm25 : float | None
        Predicted PM2.5 concentration.
        Pass None if no forecast is available.

    user_profile : str
        general, asthma, child, elderly, pregnant,
        heart_disease, outdoor_exercise
    """

    current_category = _get_pm25_category(current_pm25)

    forecast_category = (
        _get_pm25_category(forecast_pm25)
        if forecast_pm25 is not None
        else None
    )

    precautions = []

    if current_category == "Good":
        precautions.append("Air quality is good for outdoor activities.")
        mask = "No mask required."

    elif current_category == "Moderate":
        precautions.append(
            "Sensitive individuals should reduce prolonged outdoor exposure."
        )
        mask = "Mask is optional."

    elif current_category == "Unhealthy for Sensitive Groups":
        precautions.extend([
            "Reduce prolonged outdoor activity.",
            "Keep windows closed during peak pollution."
        ])
        mask = "Wear an N95 mask outdoors."

    elif current_category == "Unhealthy":
        precautions.extend([
            "Avoid outdoor exercise.",
            "Use an air purifier if available.",
            "Keep doors and windows closed."
        ])
        mask = "Wear an N95 mask whenever outdoors."

    else:
        precautions.extend([
            "Avoid going outside unless absolutely necessary.",
            "Stay indoors.",
            "Seek medical attention if breathing becomes difficult."
        ])
        mask = "An N95 mask is strongly recommended."

    profile = user_profile.lower()

    profile_messages = {
        "general": [],
        "asthma": [
            "Carry your rescue inhaler.",
            "Avoid outdoor exposure as much as possible."
        ],
        "child": [
            "Children should limit outdoor play when pollution is elevated."
        ],
        "elderly": [
            "Older adults should minimize outdoor exposure."
        ],
        "pregnant": [
            "Pregnant individuals should avoid prolonged outdoor exposure."
        ],
        "heart_disease": [
            "People with heart disease should avoid strenuous outdoor activities."
        ],
        "outdoor_exercise": [
            "Move your workout indoors if pollution is moderate or worse."
        ],
    }

    precautions.extend(
        profile_messages.get(profile, profile_messages["general"])
    )

    return {

        "success": True,

        "current_pm25": round(current_pm25, 1),

        "current_category": current_category,

        "forecast_pm25": (
            round(forecast_pm25, 1)
            if forecast_pm25 is not None
            else None
        ),

        "forecast_category": forecast_category,

        "user_profile": profile,

        "mask_recommendation": mask,

        "precautions": precautions,
    }