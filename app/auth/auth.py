# app/auth.py
from jose import jwt
from fastapi import HTTPException, Header
import httpx

SUPABASE_JWKS_URL = "https://zxzmzzhvtakcnxzzfzsk.supabase.co/auth/v1/jwks"
cached_keys = None

async def get_jwks():
    global cached_keys
    if cached_keys is None:
        async with httpx.AsyncClient() as client:
            cached_keys = (await client.get(SUPABASE_JWKS_URL)).json()
    return cached_keys

async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(401, "No token provided")

    token = authorization.replace("Bearer ", "")

    jwks = await get_jwks()

    try:
        payload = jwt.decode(token, jwks, algorithms=["RS256"], options={"verify_aud": False})
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
