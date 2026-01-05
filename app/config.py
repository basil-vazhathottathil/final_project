import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_WEB_SEARCH")
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")