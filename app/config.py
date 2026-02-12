import os
from dotenv import load_dotenv  # type: ignore

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_WEB_SEARCH")
GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

# Clerk
CLERK_ISSUER = os.getenv("CLERK_ISSUER")
CLERK_AUDIENCE = os.getenv("CLERK_AUDIENCE")
CLERK_JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"
