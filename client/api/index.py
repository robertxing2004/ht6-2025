from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# Create FastAPI app with metadata for better Swagger UI
app = FastAPI(
    title="Battery Monitoring API",
    description="API for receiving and analyzing battery telemetry data from QNX systems",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class BatteryData(BaseModel):
    timestamp: float = Field(..., description="Timestamp of the measurement")
    pack_voltage: float = Field(..., description="Battery pack voltage in volts")
    pack_current: float = Field(..., description="Battery pack current in amperes")
    cell_temp: float = Field(..., description="Cell temperature in Celsius")
    source: str = Field(..., description="Source of the data")

class BatteryResponse(BaseModel):
    message: str
    timestamp: str
    data: BatteryData

# In-memory storage for telemetry data
telemetry_data = []

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Battery Monitoring API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "battery_data": "/api/battery-data",
            "health": "/health",
            "current_data": "/api/battery/current",
            "history": "/api/battery/history"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "total_readings": len(telemetry_data),
        "last_update": telemetry_data[-1]["received_at"] if telemetry_data else None
    }

@app.post("/api/battery-data", response_model=BatteryResponse, tags=["Battery"])
async def receive_battery_data(data: BatteryData):
    """Receive battery telemetry data from QNX systems"""
    try:
        # Add timestamp and store data
        telemetry_entry = {
            "timestamp": data.timestamp,
            "pack_voltage": data.pack_voltage,
            "pack_current": data.pack_current,
            "cell_temp": data.cell_temp,
            "source": data.source,
            "received_at": datetime.now().isoformat()
        }
        
        telemetry_data.append(telemetry_entry)
        
        # Keep only last 1000 readings
        if len(telemetry_data) > 1000:
            telemetry_data.pop(0)
        
        print(f"✅ Battery data received: {telemetry_entry}")
        
        return BatteryResponse(
            message="Data received successfully",
            timestamp=telemetry_entry["received_at"],
            data=data
        )
        
    except Exception as e:
        print(f"❌ Error processing battery data: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.get("/api/battery/current", tags=["Battery"])
async def get_current_battery_data():
    """Get the most recent battery data"""
    if not telemetry_data:
        raise HTTPException(status_code=404, detail="No battery data available")
    
    return {
        "current_data": telemetry_data[-1],
        "total_readings": len(telemetry_data)
    }

@app.get("/api/battery/history", tags=["Battery"])
async def get_battery_history(limit: int = 100):
    """Get historical battery data"""
    if not telemetry_data:
        return {"history": [], "total_readings": 0}
    
    # Return the last 'limit' readings
    history = telemetry_data[-limit:] if limit > 0 else telemetry_data
    
    return {
        "history": history,
        "total_readings": len(telemetry_data),
        "returned_count": len(history)
    }

@app.get("/api/battery/stats", tags=["Battery"])
async def get_battery_stats():
    """Get battery statistics"""
    if not telemetry_data:
        raise HTTPException(status_code=404, detail="No battery data available")
    
    # Calculate statistics
    voltages = [entry["pack_voltage"] for entry in telemetry_data]
    currents = [entry["pack_current"] for entry in telemetry_data]
    temps = [entry["cell_temp"] for entry in telemetry_data]
    
    stats = {
        "total_readings": len(telemetry_data),
        "voltage": {
            "current": voltages[-1],
            "min": min(voltages),
            "max": max(voltages),
            "avg": sum(voltages) / len(voltages)
        },
        "current": {
            "current": currents[-1],
            "min": min(currents),
            "max": max(currents),
            "avg": sum(currents) / len(currents)
        },
        "temperature": {
            "current": temps[-1],
            "min": min(temps),
            "max": max(temps),
            "avg": sum(temps) / len(temps)
        },
        "last_update": telemetry_data[-1]["received_at"]
    }
    
    return stats

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Battery Monitoring API...")
    print("📍 Server: http://localhost:8000")
    print("📚 Swagger UI: http://localhost:8000/docs")
    print("📊 Battery Data: POST http://localhost:8000/api/battery-data")
    print("❤️  Health: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        access_log=True,
        log_level="info"
    )