from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.obd.ws_listener import obd_stream_handler
from app.auth.clerk_ws_auth import verify_clerk_ws
from app.db.vehicle_session import get_active_vehicle_id

router = APIRouter()


@router.websocket("/ws/obd")
async def obd_ws(websocket: WebSocket):
    """
    WebSocket endpoint for OBD data streaming.
    Vehicle context is determined from active session (no vehicle_id in path).
    """
    await websocket.accept()

    try:
        user_id = await verify_clerk_ws(websocket)

        if not user_id:
            await websocket.close(code=1008, reason="Authentication failed")
            return

        # Fetch active vehicle from session
        vehicle_id = get_active_vehicle_id(user_id)

        if not vehicle_id:
            await websocket.close(code=1008, reason="No active vehicle session")
            return

        await obd_stream_handler(
            websocket=websocket,
            user_id=user_id,
            vehicle_id=vehicle_id,
        )

    except WebSocketDisconnect:
        print("Client disconnected")
