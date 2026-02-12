"""Quick script to create test incidents - run with: uv run python quick_test.py"""
from app.db.db import supabase
from datetime import datetime
import uuid

USER_ID = "user_37b6DmEMtAX5l7DQJGcYjyFm6Wd"

print("Creating test incidents...")

# High severity incident
supabase.table("vehicle_incidents").insert({
    "id": str(uuid.uuid4()),
    "vehicle_id": "demo_vehicle_123",
    "user_id": USER_ID,
    "chat_id": str(uuid.uuid4()),
    "trigger_type": "threshold_breach",
    "trigger_metric": "COOLANT_TEMP",
    "trigger_value": 105.0,
    "trigger_limit": 100.0,
    "severity": "high",
    "snapshot": {"COOLANT_TEMP": 105, "RPM": 3200, "SPEED": 65},
    "status": "open",
    "created_at": datetime.utcnow().isoformat()
}).execute()
print("✅ High severity incident created")

# Medium severity incident
supabase.table("vehicle_incidents").insert({
    "id": str(uuid.uuid4()),
    "vehicle_id": "demo_vehicle_123",
    "user_id": USER_ID,
    "chat_id": str(uuid.uuid4()),
    "trigger_type": "threshold_breach",
    "trigger_metric": "OIL_PRESSURE",
    "trigger_value": 25.0,
    "trigger_limit": 30.0,
    "severity": "medium",
    "snapshot": {"OIL_PRESSURE": 25, "RPM": 2800, "SPEED": 55},
    "status": "open",
    "created_at": datetime.utcnow().isoformat()
}).execute()
print("✅ Medium severity incident created")

# Low severity incident
supabase.table("vehicle_incidents").insert({
    "id": str(uuid.uuid4()),
    "vehicle_id": "demo_vehicle_123",
    "user_id": USER_ID,
    "chat_id": str(uuid.uuid4()),
    "trigger_type": "threshold_breach",
    "trigger_metric": "ENGINE_LOAD",
    "trigger_value": 85.0,
    "trigger_limit": 80.0,
    "severity": "low",
    "snapshot": {"ENGINE_LOAD": 85, "RPM": 3500, "SPEED": 70},
    "status": "resolved",
    "created_at": datetime.utcnow().isoformat()
}).execute()
print("✅ Low severity incident created")

print("\n🎉 All test incidents created successfully!")
print(f"User ID: {USER_ID}")
print("\nNow open your app and navigate to /OBDIssues to see them!")
