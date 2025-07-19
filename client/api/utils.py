import json
from app.models import Battery
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "battery_data.json"

def read_battery_data() -> list[Battery]:
    with open(DATA_PATH, "r") as f:
        raw = json.load(f)
    return [Battery(**item) for item in raw]