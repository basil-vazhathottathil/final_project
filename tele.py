import asyncio

from app.obd.ws_listener import obd_stream
from app.telemetry.processor import TelemetryProcessor


async def run_test():
    print("\n🚗 Starting OBD → Telemetry test...\n")

    async for packet in obd_stream():
        pid = packet["pid"]
        decoded = packet["decoded"]

        print(f"📡 OBD PID: {pid}")
        print(f"🔎 Decoded Data: {decoded}")

        alerts = TelemetryProcessor.process(decoded)

        if alerts:
            print("🚨 ALERTS:")
            for alert in alerts:
                print(alert)
        else:
            print("✅ No alerts")

        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(run_test())
