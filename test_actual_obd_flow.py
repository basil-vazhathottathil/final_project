import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

# Mock FastAPI WebSocket
class MockWebSocket:
    def __init__(self, messages):
        self.messages = messages
        self.sent_messages = []
        self.is_closed = False

    async def receive_text(self):
        if not self.messages:
            raise Exception("No more messages")
        return self.messages.pop(0)

    async def send_json(self, data):
        self.sent_messages.append(data)

# Mock dependencies
import sys
from types import ModuleType

# Mock app.telemetry.processor
mock_processor = ModuleType("app.telemetry.processor")
mock_processor.TelemetryProcessor = MagicMock()
mock_processor.TelemetryProcessor.process.return_value = []
sys.modules["app.telemetry.processor"] = mock_processor

# Mock app.services.incident_service
mock_service = ModuleType("app.services.incident_service")
mock_service.IncidentService = MagicMock()
sys.modules["app.services.incident_service"] = mock_service

# Mock app.obd.realistic_sim
mock_sim = ModuleType("app.obd.realistic_sim")
mock_sim.realistic_obd_stream = MagicMock()
sys.modules["app.obd.realistic_sim"] = mock_sim

# Now we can import the handler
from app.obd.ws_listener import obd_stream_handler

async def test_flow():
    test_messages = [
        json.dumps({"pid": "COOLANT_TEMP", "value": 95}),
        json.dumps({"pid": "RPM", "value": 3000}),
    ]
    
    ws = MockWebSocket(test_messages)
    
    print("🚀 Starting OBD stream handler test...")
    
    # Run handler in a task so we can timeout if it hangs
    try:
        await asyncio.wait_for(
            obd_stream_handler(ws, "user_123", "vehicle_456"),
            timeout=2.0
        )
    except (asyncio.TimeoutError, Exception) as e:
        print(f"Test ended (expectedly): {e}")

    print(f"✅ Messages sent back to client: {len(ws.sent_messages)}")
    for i, msg in enumerate(ws.sent_messages):
        print(f"  [{i}] {msg}")

    assert len(ws.sent_messages) == 2
    assert "coolant_temp_c" in ws.sent_messages[0]["decoded"]
    assert "rpm" in ws.sent_messages[1]["decoded"]
    
    print("\n🎉 Test passed!")

if __name__ == "__main__":
    asyncio.run(test_flow())
