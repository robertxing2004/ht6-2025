from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class BatteryData(BaseModel):
    timestamp: float
    pack_voltage: float
    pack_current: float
    cell_temp: float
    capacity_remaining: Optional[float] = None
    cycle_count: Optional[int] = None
    age_months: Optional[float] = None
    health_score: Optional[float] = None

class BatteryPrediction(BaseModel):
    remaining_life_hours: float
    remaining_cycles: float
    degradation_rate: float

class BatteryStatus(BaseModel):
    alert_level: str  # "NORMAL", "WARNING", "CRITICAL", "ERROR"
    message: str

class BatteryStats(BaseModel):
    total_packets: int
    valid_packets: int
    error_packets: int
    avg_voltage: float
    avg_current: float
    avg_temp: float
    min_voltage_seen: float
    max_voltage_seen: float
    min_temp_seen: float
    max_temp_seen: float

class BatteryMonitorData(BaseModel):
    current_data: BatteryData
    prediction: Optional[BatteryPrediction] = None
    status: BatteryStatus
    stats: BatteryStats
    history: List[BatteryData]

# Legacy model for backward compatibility
class Battery(BaseModel):
    battery_id: str
    timestamp: str
    state_of_health: float
    capacity_mAh: float
    internal_resistance_mOhm: float
    temperature_C: float
    cycle_count: int
    status: str