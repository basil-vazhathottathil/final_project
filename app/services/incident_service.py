from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

from app.db.db import supabase
from app.agent.vehicle_agent import run_vehicle_agent


class IncidentService:

    @staticmethod
    def create_incident(
        user_id: str,
        vehicle_id: str,
        snapshot: Dict[str, Any],
        alert: Dict[str, Any],
    ) -> Dict[str, Any]:

        # Generate IDs
        incident_id = str(uuid4())
        chat_id = uuid4()

        # -----------------------------
        # 1️⃣ Insert into vehicle_incidents
        # -----------------------------
        supabase.table("vehicle_incidents").insert({
            "id": incident_id,
            "vehicle_id": vehicle_id,
            "user_id": user_id,
            "chat_id": str(chat_id),
            "trigger_type": alert.get("type"),
            "trigger_metric": alert.get("metric"),
            "trigger_value": alert.get("value"),
            "trigger_limit": alert.get("limit"),
            "severity": alert.get("severity"),
            "snapshot": snapshot,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        # -----------------------------
        # 2️⃣ Convert snapshot → agent input
        # -----------------------------
        user_input = f"""
AUTOMATIC VEHICLE ALERT

Trigger:
{alert}

Snapshot:
{snapshot}

This alert was generated automatically from live OBD data.
Explain:
1. What is happening
2. Severity level
3. Whether the driver can continue driving
4. Immediate precautions
"""

        # -----------------------------
        # 3️⃣ Call agent (reusing your existing system)
        # -----------------------------
        agent_response = run_vehicle_agent(
            user_input=user_input,
            chat_id=chat_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
        )

        # IMPORTANT:
        # run_vehicle_agent already stores chat turn via save_chat_turn()
        # So we DO NOT manually insert into ai_chat_history again.

        return {
            "incident_id": incident_id,
            "chat_id": str(chat_id),
            "agent_response": agent_response,
        }
