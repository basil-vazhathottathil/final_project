from fastapi import FastAPI, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import JSONResponse, Response # type: ignore
import logging

from app.routers import vehicle_chat, vehicle_workshops
from app.routers.maintenance_route import router as maintenance_router

# App
app = FastAPI(
    title="Vehicle Repair AI Agent",
    version="0.4.0",
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Preflight OPTIONS (keep this)
@app.middleware("http")
async def preflight_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(status_code=204)
    return await call_next(request)

# CORS (FINAL, CORRECT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "https://finalproject-production-fcdc.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler (DO NOT hardcode origin)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
    )

# Health
@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/version")
async def version():
    return {"version": app.version}

# Routers
app.include_router(vehicle_chat.router)
app.include_router(vehicle_workshops.router)
app.include_router(maintenance_router)

# Lifecycle
@app.on_event("startup")
async def startup():
    logger.info("Vehicle Agent started")
    logger.info("CORS enabled for localhost and Railway")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Vehicle Agent stopped")
