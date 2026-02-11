# app/telemetry/processor.py

from typing import Dict, List

from app.telemetry.thresholds import THRESHOLDS
from app.telemetry.cooldown import CooldownManager


cooldown = CooldownManager()


class TelemetryProcessor:
    @staticmethod
    def process(decoded_data: Dict) -> List[Dict]:
        alerts = []

        for metric, value in decoded_data.items():
            if metric not in THRESHOLDS:
                continue

            limit = THRESHOLDS[metric].get("max")
            if limit is None:
                continue

            if value > limit:
                alert_key = f"{metric}_high"

                if cooldown.can_trigger(alert_key):
                    alerts.append(
                        {
                            "type": "THRESHOLD_BREACH",
                            "metric": metric,
                            "value": value,
                            "limit": limit,
                            "severity": TelemetryProcessor._severity(value, limit),
                        }
                    )

        return alerts

    @staticmethod
    def _severity(value: float, limit: float) -> float:
        ratio = value / limit
        return min(round((ratio - 1) * 2, 2), 1.0)
