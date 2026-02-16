from app.db.db import supabase
from datetime import datetime
from uuid import uuid4

# Your Clerk user ID (extracted from JWT token)
YOUR_USER_ID = "user_37b6DmEMtAX5l7DQJGcYjyFm6Wd"

# Create 3 test incidents with different severities
incidents = [
    {
        "id": str(uuid4()),
        "vehicle_id": "demo_vehicle_123",
        "user_id": YOUR_USER_ID,
        "chat_id": str(uuid4()),
        "trigger_type": "threshold_breach",
        "trigger_metric": "COOLANT_TEMP",
        "trigger_value": 105.0,
        "trigger_limit": 100.0,
        "severity": "high",
        "snapshot": {
            "COOLANT_TEMP": 105,
            "RPM": 3200,
            "SPEED": 65,
            "ENGINE_LOAD": 75
        },
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid4()),
        "vehicle_id": "demo_vehicle_123",
        "user_id": YOUR_USER_ID,
        "chat_id": str(uuid4()),
        "trigger_type": "threshold_breach",
        "trigger_metric": "OIL_PRESSURE",
        "trigger_value": 25.0,
        "trigger_limit": 30.0,
        "severity": "medium",
        "snapshot": {
            "OIL_PRESSURE": 25,
            "RPM": 2800,
            "SPEED": 55,
            "ENGINE_LOAD": 60
        },
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": str(uuid4()),
        "vehicle_id": "demo_vehicle_123",
        "user_id": YOUR_USER_ID,
        "chat_id": str(uuid4()),
        "trigger_type": "threshold_breach",
        "trigger_metric": "ENGINE_LOAD",
        "trigger_value": 85.0,
        "trigger_limit": 80.0,
        "severity": "low",
        "snapshot": {
            "ENGINE_LOAD": 85,
            "RPM": 3500,
            "SPEED": 70,
            "COOLANT_TEMP": 92
        },
        "status": "resolved",
        "created_at": datetime.utcnow().isoformat()
    }
]

# Insert each incident
for incident in incidents:
    result = supabase.table("vehicle_incidents").insert(incident).execute()
    print(f"✅ Created {incident['severity']} severity incident: {incident['trigger_metric']}")

print("\n✨ All test incidents created successfully!")
