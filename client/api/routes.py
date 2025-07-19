from fastapi import APIRouter, HTTPException
from app.utils import read_battery_data
from app.models import Battery

router = APIRouter()

@router.get("/api/batteries", response_model=list[Battery])
def get_batteries():
    try:
        return read_battery_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/batteries/{battery_id}", response_model=Battery)
def get_battery(battery_id: str):
    batteries = read_battery_data()
    for batt in batteries:
        if batt.battery_id == battery_id:
            return batt
    raise HTTPException(status_code=404, detail="Battery not found")