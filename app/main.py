from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

from app.routers import vehicle_chat, vehicle_workshops
from app.routers.maintenance_route import router as maintenance_router

app = FastAPI(
    title="Vehicle Repair AI Agent",
    version="0.4.0"
)

# ---- CORS ----

raw_origins = os.getenv("CORS_ORIGINS", "")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)

# ---- Logging ----

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Health ----

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/version")
async def version():
    return {"version": app.version}

# ---- Routers ----

app.include_router(vehicle_chat.router)
app.include_router(vehicle_workshops.router)
app.include_router(maintenance_router)

# ---- Lifecycle ----

@app.on_event("startup")
async def startup():
    logger.info("Agent started")
    logger.info("CORS allowed origins: %s", allowed_origins)

@app.on_event("shutdown")
async def shutdown():
    logger.info("Agent stopped")
