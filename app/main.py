from fastapi import FastAPI # type: ignore

from app.routers import vehicle_chat, vehicle_workshops

app = FastAPI(title="Vehicle Repair AI Agent")


@app.get("/")
async def health():
    return {"status": "ok"}


# 🔹 Register routers
app.include_router(vehicle_chat.router)
app.include_router(vehicle_workshops.router)
