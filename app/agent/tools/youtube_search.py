import re
from typing import List
from app.agent.tools.web_search import get_web_search_tool

def normalize_youtube_url(url: str) -> str | None:
    """
    Ensures the URL is a standard mobile-friendly YouTube watch URL.
    """
    video_id = None
    
    if "v=" in url:
        match = re.search(r"v=([0-9A-Za-z_-]{11})", url)
        if match:
            video_id = match.group(1)
    elif "youtu.be/" in url:
        match = re.search(r"youtu\.be\/([0-9A-Za-z_-]{11})", url)
        if match:
            video_id = match.group(1)
    else:
        # Fallback for /v/ or /embed/
        match = re.search(r"(?:\/v\/|\/embed\/)([0-9A-Za-z_-]{11})", url)
        if match:
            video_id = match.group(1)

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return None

def search_youtube_videos(diagnosis: str) -> List[str]:
    """
    Searches for YouTube DIY repair videos based on a diagnosis.
    Returns a list of unique, mobile-friendly YouTube URLs.
    """
    search_tool = get_web_search_tool()
    query = f"{diagnosis} car DIY repair youtube"
    
    try:
        results = search_tool.invoke(query)
        youtube_urls = []
        seen_ids = set()
        
        for result in results:
            url = result.get("url", "")
            if "youtube.com" in url or "youtu.be" in url:
                normalized = normalize_youtube_url(url)
                if normalized:
                    # Extract ID to avoid duplicates
                    video_id = normalized.split("v=")[-1]
                    if video_id not in seen_ids:
                        youtube_urls.append(normalized)
                        seen_ids.add(video_id)
        
        return youtube_urls[:3]  # Return top 3
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []
