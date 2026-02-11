# app/obd/realistic_simulator.py

import asyncio
import random
from typing import Dict


class RealisticOBDSimulator:
    """
    Simulates realistic car driving behavior.
    """

    def __init__(self):
        self.speed = 0
        self.rpm = 800
        self.coolant_temp = 25  # cold start
        self.engine_load = 10
        self.throttle = 5
        self.time_running = 0
        self.overheat_triggered = False

    def _update_engine_warmup(self):
        if self.coolant_temp < 92:
            self.coolant_temp += random.uniform(0.2, 0.8)

    def _update_driving_pattern(self):
        # Simulate acceleration / deceleration phases
        phase = (self.time_running // 20) % 3

        if phase == 0:  # accelerating
            self.speed += random.uniform(0, 3)
        elif phase == 1:  # cruising
            self.speed += random.uniform(-1, 1)
        else:  # slowing down
            self.speed -= random.uniform(0, 2)

        self.speed = max(0, min(self.speed, 120))

    def _update_rpm(self):
        base_rpm = 800 + (self.speed * 35)
        self.rpm = int(base_rpm + random.uniform(-150, 150))
        self.rpm = max(700, min(self.rpm, 5000))

    def _update_engine_load(self):
        self.engine_load = min(100, max(10, (self.rpm / 50) + random.uniform(-5, 5)))

    def _update_throttle(self):
        self.throttle = min(100, max(5, self.engine_load / 1.2))

    def _maybe_trigger_overheat(self):
        # After 90 seconds, 20% chance of overheat event
        if self.time_running > 90 and not self.overheat_triggered:
            if random.random() < 0.2:
                print("🔥 SIMULATED OVERHEAT EVENT")
                self.coolant_temp = 110
                self.overheat_triggered = True

    def step(self) -> Dict[str, float]:
        self.time_running += 1

        self._update_engine_warmup()
        self._update_driving_pattern()
        self._update_rpm()
        self._update_engine_load()
        self._update_throttle()
        self._maybe_trigger_overheat()

        return {
            "speed_kmph": round(self.speed, 1),
            "rpm": self.rpm,
            "coolant_temp_c": round(self.coolant_temp, 1),
            "engine_load_pct": round(self.engine_load, 1),
            "throttle_pct": round(self.throttle, 1),
        }


async def realistic_obd_stream():
    simulator = RealisticOBDSimulator()

    while True:
        yield simulator.step()
        await asyncio.sleep(1)
