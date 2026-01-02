import os
import requests
from langchain.tools import Tool

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


def _find_nearby_workshops(lat: float, lng: float) -> str:
    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "keyword": "car repair garage",
        "key": GOOGLE_MAPS_KEY,
    }

    res = requests.get(PLACES_URL, params=params, timeout=10)
    data = res.json()

    results = data.get("results", [])[:5]

    if not results:
        return "No nearby workshops found."

    text = "🔧 Nearby workshops:\n"
    for place in results:
        maps_link = (
            "https://www.google.com/maps/search/?api=1"
            f"&query_place_id={place['place_id']}"
        )
        text += f"- {place['name']}: {maps_link}\n"

    return text


def get_workshop_tool():
    return Tool(
        name="find_nearby_workshops",
        func=_find_nearby_workshops,
        description=(
            "Use this tool to find nearby car repair workshops, garages, "
            "service centers, or mechanics when the user asks for them. "
            "Requires latitude and longitude."
        ),
    )
