from fastapi import Request
from fastapi.responses import Response

async def preflight_middleware(request: Request, call_next):
    # Let CORS middleware handle headers, just unblock OPTIONS
    if request.method == "OPTIONS":
        return Response(status_code=204)

    return await call_next(request)
