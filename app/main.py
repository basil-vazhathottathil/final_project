from fastapi import FastAPI
import logging

from app.routers import vehicle_chat, vehicle_workshops
from app.routers.maintenance_route import router as maintenance_router

# App setup
app = FastAPI(
    title="Vehicle Repair AI Agent",
    version="0.4.0"
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Health endpoints
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

# Lifecycle logs
@app.on_event("startup")
async def startup():
    logger.info("Agent started")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Agent stopped")
