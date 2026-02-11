# app/telemetry/cooldown.py

import time
from typing import Dict


class CooldownManager:
    def __init__(self, cooldown_seconds: int = 300):
        self.cooldown_seconds = cooldown_seconds
        self._last_triggered: Dict[str, float] = {}

    def can_trigger(self, key: str) -> bool:
        now = time.time()
        last = self._last_triggered.get(key, 0)

        if now - last >= self.cooldown_seconds:
            self._last_triggered[key] = now
            return True

        return False
