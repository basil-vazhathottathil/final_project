# app/obd/decoder.py

from typing import Dict, Any


class OBDDecoder:
    """
    Decodes raw OBD-II PID values into human-readable metrics.
    """

    @staticmethod
    def decode(pid: str, value: Any) -> Dict[str, Any]:
        try:
            if pid == "SPEED":
                return {"speed_kmph": float(value)}

            if pid == "RPM":
                return {"rpm": int(value)}

            if pid == "COOLANT_TEMP":
                return {"coolant_temp_c": float(value)}

            if pid == "ENGINE_LOAD":
                return {"engine_load_pct": float(value)}

            if pid == "THROTTLE_POS":
                return {"throttle_pct": float(value)}

            if pid == "DISTANCE_SINCE_DTC_CLEAR":
                return {"distance_since_dtc_clear_km": float(value)}

            # Unknown PID fallback
            return {"raw_pid": pid, "value": value}

        except Exception:
            return {"error": f"Failed to decode PID {pid}", "raw_value": value}
