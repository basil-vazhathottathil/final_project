# app/obd/ws_listener.py

import asyncio
import random
from typing import AsyncGenerator, Dict

from app.obd.decoder import OBDDecoder


SUPPORTED_PIDS = [
    "SPEED",
    "RPM",
    "COOLANT_TEMP",
    "ENGINE_LOAD",
    "THROTTLE_POS",
]


async def obd_stream() -> AsyncGenerator[Dict, None]:
    """
    Simulated OBD data stream.
    Replace this with real WebSocket / Bluetooth logic later.
    """
    while True:
        pid = random.choice(SUPPORTED_PIDS)

        if pid == "SPEED":
            value = random.randint(0, 120)
        elif pid == "RPM":
            value = random.randint(700, 4500)
        elif pid == "COOLANT_TEMP":
            value = random.randint(70, 115)
        elif pid == "ENGINE_LOAD":
            value = random.randint(10, 90)
        elif pid == "THROTTLE_POS":
            value = random.randint(5, 80)
        else:
            value = 0

        decoded = OBDDecoder.decode(pid, value)

        yield {
            "pid": pid,
            "decoded": decoded,
        }

        await asyncio.sleep(1)
