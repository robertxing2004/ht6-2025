from pydantic import BaseModel
from datetime import datetime

class Battery(BaseModel):
    battery_id: str
    timestamp: str  # or use datetime if your data is ISO format
    state_of_health: float
    capacity_mAh: float
    internal_resistance_mOhm: float
    temperature_C: float
    cycle_count: int
    status: str  # "charging" or "discharging"