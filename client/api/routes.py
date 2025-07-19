from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from app.utils import read_battery_data, get_simulated_battery_data
from app.models import Battery, BatteryMonitorData, BatteryData, BatteryPrediction, BatteryStatus, BatteryStats
import json
import asyncio
from typing import List
import random
import time

router = APIRouter()

# Simulated data for development (replace with actual C++ monitor connection)
class BatteryMonitorSimulator:
    def __init__(self):
        self.current_data = BatteryData(
            timestamp=time.time(),
            pack_voltage=355.2,
            pack_current=25.5,
            cell_temp=25.0,
            capacity_remaining=85.0,
            cycle_count=150,
            age_months=6.0,
            health_score=92.0
        )
        self.stats = BatteryStats(
            total_packets=1000,
            valid_packets=985,
            error_packets=15,
            avg_voltage=354.8,
            avg_current=24.2,
            avg_temp=24.5,
            min_voltage_seen=320.0,
            max_voltage_seen=370.0,
            min_temp_seen=15.0,
            max_temp_seen=45.0
        )
        self.prediction = BatteryPrediction(
            remaining_life_hours=156.7,
            remaining_cycles=342,
            degradation_rate=0.085
        )
        self.history = []
        self._generate_history()
    
    def _generate_history(self):
        """Generate simulated historical data"""
        base_time = time.time() - 3600  # Last hour
        for i in range(60):
            self.history.append(BatteryData(
                timestamp=base_time + i * 60,
                pack_voltage=355.0 + random.uniform(-5, 5),
                pack_current=25.0 + random.uniform(-10, 10),
                cell_temp=25.0 + random.uniform(-3, 3),
                capacity_remaining=85.0 - i * 0.1,
                cycle_count=150,
                age_months=6.0,
                health_score=92.0 - i * 0.05
            ))
    
    def update_data(self):
        """Simulate real-time data updates"""
        # Simulate voltage fluctuations
        self.current_data.pack_voltage += random.uniform(-0.5, 0.5)
        self.current_data.pack_voltage = max(320.0, min(370.0, self.current_data.pack_voltage))
        
        # Simulate current changes
        self.current_data.pack_current += random.uniform(-2, 2)
        self.current_data.pack_current = max(-50, min(50, self.current_data.pack_current))
        
        # Simulate temperature changes
        self.current_data.cell_temp += random.uniform(-0.5, 0.5)
        self.current_data.cell_temp = max(15.0, min(45.0, self.current_data.cell_temp))
        
        # Update timestamp
        self.current_data.timestamp = time.time()
        
        # Update capacity and health
        self.current_data.capacity_remaining = max(0, self.current_data.capacity_remaining - 0.01)
        self.current_data.health_score = max(0, self.current_data.health_score - 0.001)
        
        # Add to history
        self.history.append(self.current_data)
        if len(self.history) > 1000:
            self.history.pop(0)
        
        # Update stats
        self.stats.total_packets += 1
        self.stats.valid_packets += 1
    
    def get_status(self) -> BatteryStatus:
        """Determine battery status based on current data"""
        if (self.current_data.pack_voltage < 330.0 or 
            self.current_data.pack_voltage > 365.0 or
            self.current_data.cell_temp > 40.0 or
            self.current_data.health_score < 80.0):
            return BatteryStatus(alert_level="CRITICAL", message="Battery parameters outside safe range")
        elif (self.current_data.pack_voltage < 340.0 or 
              self.current_data.pack_current > 40.0 or
              self.current_data.cell_temp > 35.0):
            return BatteryStatus(alert_level="WARNING", message="Battery parameters approaching limits")
        else:
            return BatteryStatus(alert_level="NORMAL", message="Battery operating normally")

# Global simulator instance
simulator = BatteryMonitorSimulator()

@router.get("/api/batteries", response_model=List[Battery])
def get_batteries():
    """Legacy endpoint for backward compatibility"""
    try:
        return read_battery_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/batteries/{battery_id}", response_model=Battery)
def get_battery(battery_id: str):
    """Legacy endpoint for backward compatibility"""
    batteries = read_battery_data()
    for batt in batteries:
        if batt.battery_id == battery_id:
            return batt
    raise HTTPException(status_code=404, detail="Battery not found")

@router.get("/api/battery/current", response_model=BatteryData)
def get_current_battery_data():
    """Get current battery data"""
    simulator.update_data()
    return simulator.current_data

@router.get("/api/battery/prediction", response_model=BatteryPrediction)
def get_battery_prediction():
    """Get AI battery life prediction"""
    return simulator.prediction

@router.get("/api/battery/status", response_model=BatteryStatus)
def get_battery_status():
    """Get current battery status and alerts"""
    return simulator.get_status()

@router.get("/api/battery/stats", response_model=BatteryStats)
def get_battery_stats():
    """Get battery monitoring statistics"""
    return simulator.stats

@router.get("/api/battery/history", response_model=List[BatteryData])
def get_battery_history(limit: int = 100):
    """Get battery data history"""
    return simulator.history[-limit:]

@router.get("/api/battery/monitor", response_model=BatteryMonitorData)
def get_battery_monitor_data():
    """Get complete battery monitoring data"""
    simulator.update_data()
    return BatteryMonitorData(
        current_data=simulator.current_data,
        prediction=simulator.prediction,
        status=simulator.get_status(),
        stats=simulator.stats,
        history=simulator.history[-100:]  # Last 100 readings
    )

# WebSocket for real-time updates
@router.websocket("/ws/battery")
async def websocket_battery_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Update simulator data
            simulator.update_data()
            
            # Send complete monitoring data
            monitor_data = BatteryMonitorData(
                current_data=simulator.current_data,
                prediction=simulator.prediction,
                status=simulator.get_status(),
                stats=simulator.stats,
                history=simulator.history[-50:]  # Last 50 readings for real-time
            )
            
            await websocket.send_text(monitor_data.model_dump_json())
            
            # Wait 1 second before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()