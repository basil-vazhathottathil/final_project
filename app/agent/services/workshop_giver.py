import os
import requests
from langchain_core.tools import Tool

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")
PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


def _build_maps_url(place_id: str) -> str:
    return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


def _find_nearby_workshops(input: dict) -> dict:
    """
    Expected input:
    {
        "latitude": float,
        "longitude": float
    }
    """

    lat = input.get("latitude")
    lng = input.get("longitude")

    if lat is None or lng is None:
        return {"error": "LOCATION_REQUIRED"}

    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "keyword": "car repair garage",
        "key": GOOGLE_MAPS_KEY,
    }

    try:
        res = requests.get(PLACES_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception:
        return {"maps_urls": []}

    results = data.get("results", [])[:5]

    maps_urls = []
    for place in results:
        place_id = place.get("place_id")
        if place_id:
            maps_urls.append(_build_maps_url(place_id))

    return {
        "maps_urls": maps_urls
    }


def get_workshop_tool():
    return Tool(
        name="find_nearby_workshops",
        func=_find_nearby_workshops,
        description=(
            "Find nearby car repair workshops and garages. "
            "Input must be a JSON object with keys "
            "`latitude` (float) and `longitude` (float). "
            "Returns a JSON object with `maps_urls`."
        ),
    )
