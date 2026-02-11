from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.obd.ws_listener import obd_stream_handler
from app.auth.clerk_ws_auth import verify_clerk_ws

router = APIRouter()


@router.websocket("/ws/obd/{vehicle_id}")
async def obd_ws(websocket: WebSocket, vehicle_id: str):

    await websocket.accept()

    try:
        user_id = await verify_clerk_ws(websocket)

        if not user_id:
            return

        await obd_stream_handler(
            websocket=websocket,
            user_id=user_id,
            vehicle_id=vehicle_id,
        )

    except WebSocketDisconnect:
        print("Client disconnected")
