# app/auth.py
from jose import jwt  # type: ignore
from fastapi import HTTPException, Header  # type: ignore
import httpx  # type: ignore
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

# 🔐 Load from environment
CLERK_ISSUER = os.getenv("CLERK_ISSUER")
CLERK_AUDIENCE = os.getenv("CLERK_AUDIENCE", "clerk")

if not CLERK_ISSUER:
    raise RuntimeError("CLERK_ISSUER is not set in .env")

# Derived value (do NOT store in .env)
CLERK_JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"

cached_keys = None


async def get_jwks():
    global cached_keys
    if cached_keys is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(CLERK_JWKS_URL)
            resp.raise_for_status()
            cached_keys = resp.json()
    return cached_keys


async def verify_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")

    token = authorization.replace("Bearer ", "").strip()

    jwks = await get_jwks()

    try:
        # Extract key id from token header
        header = jwt.get_unverified_header(token)
        key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=CLERK_AUDIENCE,
            issuer=CLERK_ISSUER,
        )

        return payload

    except StopIteration:
        raise HTTPException(status_code=401, detail="Invalid token key")

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user_id(
    authorization: str = Header(None),
) -> str:
    payload = await verify_token(authorization)
    return payload["sub"]
