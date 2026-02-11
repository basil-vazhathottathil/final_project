import httpx
from jose import jwt
from fastapi import WebSocket

from app.config import CLERK_JWKS_URL, CLERK_ISSUER, CLERK_AUDIENCE


_jwks_cache = None


async def get_jwks():
    global _jwks_cache

    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(CLERK_JWKS_URL)
            _jwks_cache = response.json()

    return _jwks_cache


async def verify_clerk_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return None

    try:
        jwks = await get_jwks()

        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=CLERK_AUDIENCE,
            issuer=CLERK_ISSUER,
        )

        return payload.get("sub")

    except Exception:
        await websocket.close(code=1008)
        return None
