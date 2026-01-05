import requests
from typing import List

from langchain_core.tools import Tool
from tavily import TavilyClient

from app.config import GOOGLE_MAPS_KEY, TAVILY_API_KEY


PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

tavily = TavilyClient(api_key=TAVILY_API_KEY)


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def build_place_url(place_id: str) -> str:
    """
    Builds the exact Google Maps Place Details page URL
    (Directions / Call / Reviews / Photos)
    """
    return f"https://www.google.com/maps/place/?q=place_id:{place_id}"


def extract_maps_place_links_from_web(lat: float, lng: float) -> List[str]:
    """
    Web-search fallback.
    Only accepts real Google Maps *place pages*.
    """
    try:
        query = (
            f"car workshop garage service center near "
            f"{lat},{lng} site:google.com/maps"
        )

        res = tavily.search(query=query, max_results=10)

        links: List[str] = []
        for r in res.get("results", []):
            url = r.get("url", "")
            if (
                "google.com/maps/place" in url
                or "maps.google.com/?cid=" in url
            ):
                links.append(url)

        # dedupe while preserving order
        return list(dict.fromkeys(links))[:5]

    except Exception:
        return []


# -------------------------------------------------
# Core service
# -------------------------------------------------

def _find_nearby_workshops(input: dict) -> dict:
    """
    Expected input:
    {
        "latitude": float,
        "longitude": float
    }

    Returns:
    {
        "maps_urls": [ list of Google Maps place-page URLs ]
    }
    """

    lat = input.get("latitude")
    lng = input.get("longitude")

    if lat is None or lng is None:
        return {"maps_urls": []}

    # ---------- 1️⃣ Google Places API (PRIMARY) ----------
    params = {
        "location": f"{lat},{lng}",
        "radius": 5000,
        "type": "car_repair",
        "keyword": "garage workshop service center mechanic",
        "key": GOOGLE_MAPS_KEY,
    }

    try:
        res = requests.get(PLACES_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        # print("GOOGLE_MAPS_KEY LOADED:", bool(GOOGLE_MAPS_KEY))
        # print("PLACES REQUEST PARAMS:", params)
        # print("PLACES RAW RESPONSE:", data)


        results = data.get("results", [])

        if results:
            maps_urls: List[str] = []
            for place in results[:5]:
                place_id = place.get("place_id")
                if place_id:
                    maps_urls.append(build_place_url(place_id))

            if maps_urls:
                return {"maps_urls": maps_urls}

    except Exception:
        # silent fail → fallback
        pass

    # ---------- 2️⃣ Web-search fallback (SECONDARY) ----------
    maps_urls = extract_maps_place_links_from_web(lat, lng)
    return {"maps_urls": maps_urls}


# -------------------------------------------------
# Tool wrapper (used by endpoint, not by agent)
# -------------------------------------------------

def get_workshop_tool():
    return Tool(
        name="find_nearby_workshops",
        func=_find_nearby_workshops,
        description=(
            "Returns Google Maps place-page URLs for nearby vehicle workshops. "
            "Input must contain latitude and longitude."
        ),
    )
