# app/obd/ws_listener.py

import asyncio
from fastapi import WebSocket

from app.telemetry.processor import TelemetryProcessor
from app.services.incident_service import IncidentService
from app.obd.realistic_sim import realistic_obd_stream

# from app.obd.decoder import OBDDecoder   # 🔹 Needed for real OBD
# import json                               # 🔹 Needed for real WebSocket input


async def obd_stream_handler(
    websocket: WebSocket,
    user_id: str,
    vehicle_id: str,
):
    """
    Handles live OBD stream.

    Currently uses realistic simulator.
    Real OBD integration code is preserved as comments.
    """

    try:
        # ==============================
        # 🔹 SIMULATED REALISTIC STREAM
        # ==============================

        async for decoded in realistic_obd_stream():

            # 🔍 Run telemetry threshold checks
            alerts = TelemetryProcessor.process(decoded)

            # 🚨 Create incidents if thresholds breached
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
                "decoded": decoded,
                "alerts": alerts,
            })

        # ==========================================
        # 🔹 REAL OBD IMPLEMENTATION (FUTURE USE)
        # ==========================================
        #
        # while True:
        #
        #     # 1️⃣ Receive raw OBD message from client/device
        #     raw_message = await websocket.receive_text()
        #
        #     # Example raw format:
        #     # {"pid": "COOLANT_TEMP", "value": 105}
        #
        #     data = json.loads(raw_message)
        #
        #     pid = data.get("pid")
        #     value = data.get("value")
        #
        #     # 2️⃣ Decode PID
        #     decoded = OBDDecoder.decode(pid, value)
        #
        #     # 3️⃣ Run telemetry
        #     alerts = TelemetryProcessor.process(decoded)
        #
        #     # 4️⃣ Trigger incident if needed
        #     for alert in alerts:
        #         IncidentService.create_incident(
        #             user_id=user_id,
        #             vehicle_id=vehicle_id,
        #             snapshot=decoded,
        #             alert=alert,
        #         )
        #
        #     # 5️⃣ Send processed result back
        #     await websocket.send_json({
        #         "decoded": decoded,
        #         "alerts": alerts,
        #     })
        #

    except Exception as e:
        print("WebSocket error:", e)

    finally:
        print("WebSocket connection closed")
