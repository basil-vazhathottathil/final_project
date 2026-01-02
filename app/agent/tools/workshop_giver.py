import os
import requests
from typing import List, Dict

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

def find_nearby_workshops(lat: float, lng: float, radius: int = 5000) -> List[Dict]:
    """
    Find nearby vehicle repair workshops using Google Places API.
    """
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": "car repair garage",
        "key": GOOGLE_MAPS_KEY,
    }

    res = requests.get(PLACES_URL, params=params, timeout=10)
    data = res.json()

    workshops = []
    for place in data.get("results", [])[:5]:
        workshops.append({
            "name": place["name"],
            "maps_link": (
                "https://www.google.com/maps/search/?api=1"
                f"&query_place_id={place['place_id']}"
            )
        })

    return workshops
