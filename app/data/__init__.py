import json
from pathlib import Path

OBD_CODES = json.loads(
    Path(__file__).with_name("obd_codes_refined.json").read_text(encoding="utf-8")
)
