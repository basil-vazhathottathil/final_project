# app/obd/ws_listener.py

import asyncio
import random
from typing import Dict

from fastapi import WebSocket

from app.obd.decoder import OBDDecoder
from app.telemetry.processor import TelemetryProcessor
from app.services.incident_service import IncidentService


SUPPORTED_PIDS = [
    "SPEED",
    "RPM",
    "COOLANT_TEMP",
    "ENGINE_LOAD",
    "THROTTLE_POS",
]


async def obd_stream_handler(
    websocket: WebSocket,
    user_id: str,
    vehicle_id: str,
):
    """
    Handles live OBD stream for an authenticated user + vehicle.
    """

    try:
        while True:
            pid = random.choice(SUPPORTED_PIDS)

            if pid == "SPEED":
                value = random.randint(0, 120)
            elif pid == "RPM":
                value = random.randint(700, 4500)
            elif pid == "COOLANT_TEMP":
                value = random.randint(70, 115)
            elif pid == "ENGINE_LOAD":
                value = random.randint(10, 90)
            elif pid == "THROTTLE_POS":
                value = random.randint(5, 80)
            else:
                value = 0

            decoded = OBDDecoder.decode(pid, value)

            # 🔍 Run telemetry
            alerts = TelemetryProcessor.process(decoded)

            # 🚨 Create incident if needed
            for alert in alerts:
                print("🚨 ALERT TRIGGERED:", alert)

                IncidentService.create_incident(
                    user_id=user_id,
                    vehicle_id=vehicle_id,
                    snapshot=decoded,
                    alert=alert,
                )

            # 📡 Send live data to frontend
            await websocket.send_json({
                "pid": pid,
                "decoded": decoded,
                "alerts": alerts,
            })

            await asyncio.sleep(1)

    except Exception as e:
        print("WebSocket disconnected:", e)
