from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os
import logging

from app.routers import vehicle_chat, vehicle_workshops
from app.routers.maintenance_route import router as maintenance_router

app = FastAPI(
    title="Vehicle Repair AI Agent",
    version="0.4.0"
)

# --------------------------------------------------
# PRE-FLIGHT HANDLER (MUST COME FIRST)
# --------------------------------------------------

@app.middleware("http")
async def allow_preflight(request: Request, call_next):
    if request.method == "OPTIONS":
        return Response(status_code=204)
    return await call_next(request)

# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/version")
async def version():
    return {"version": app.version}

# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(vehicle_chat.router)
app.include_router(vehicle_workshops.router)
app.include_router(maintenance_router)

# --------------------------------------------------
# Lifecycle
# --------------------------------------------------

@app.on_event("startup")
async def startup():
    logger.info("Agent started")
    logger.info("CORS enabled for localhost:8081")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Agent stopped")
