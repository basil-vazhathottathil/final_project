import requests
from typing import List

from langchain_core.tools import Tool # type: ignore
from tavily import TavilyClient # type: ignore

from app.config import GOOGLE_MAPS_KEY, TAVILY_API_KEY


PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

tavily = TavilyClient(api_key=TAVILY_API_KEY)


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def build_place_url(place_id: str, name: str = "", lat: float = None, lng: float = None) -> str:
    """
    Google Maps link that reliably opens in Maps app on mobile.
    Uses direct maps.google.com URL with coordinates and place name.
    On mobile: Opens in Google Maps app if installed, otherwise browser.
    On desktop: Opens in browser.
    """
    if lat and lng and name:
        # Use coordinates + name - most reliable for mobile
        encoded_name = name.replace(" ", "+")
        return f"https://maps.google.com/?q={lat},{lng}+({encoded_name})"
    else:
        # Fallback to place_id only
        return f"https://maps.google.com/?q=place_id:{place_id}"


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

        results = data.get("results", [])

        if results:
            maps_urls: List[str] = []
            for place in results[:5]:
                place_id = place.get("place_id")
                name = place.get("name", "")
                geometry = place.get("geometry", {})
                location = geometry.get("location", {})
                place_lat = location.get("lat")
                place_lng = location.get("lng")
                
                if place_id:
                    # Build URL with all available data for best mobile experience
                    url = build_place_url(place_id, name, place_lat, place_lng)
                    maps_urls.append(url)

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
