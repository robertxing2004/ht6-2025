from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import motor.motor_asyncio
from datetime import datetime, timedelta
import asyncio
import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
from battery_ai_predictor import BatteryAIPredictor, BatteryPerformance as AIPerformance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Battery Monitoring API",
    description="API for storing and retrieving battery data from QNX monitoring system",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Atlas connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://ht62025:ht62025@cluster0.qnxyebq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = "battery_db"

# Initialize MongoDB client
try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    logger.info("Connected to MongoDB Atlas")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    client = None
    db = None

# Initialize AI Predictor
ai_predictor = None
try:
    ai_predictor = BatteryAIPredictor(mongo_uri=MONGODB_URI)
    logger.info("AI Predictor initialized")
except Exception as e:
    logger.error(f"Failed to initialize AI Predictor: {e}")

# Pydantic models for data validation
class BatteryData(BaseModel):
    timestamp: float = Field(..., description="Unix timestamp")
    pack_voltage: float = Field(..., description="Pack voltage in volts")
    pack_current: float = Field(..., description="Pack current in amps")
    cell_temp: float = Field(..., description="Cell temperature in Celsius")
    source: str = Field(default="battery_monitor", description="Data source")

class BatteryPerformance(BaseModel):
    timestamp: float = Field(..., description="Unix timestamp")
    pack_voltage: float = Field(..., description="Pack voltage in volts")
    pack_current: float = Field(..., description="Pack current in amps")
    cell_temp: float = Field(..., description="Cell temperature in Celsius")
    capacity_remaining: float = Field(..., description="Capacity remaining in percentage")
    cycle_count: int = Field(..., description="Total cycle count")
    age_months: float = Field(..., description="Battery age in months")
    health_score: float = Field(..., description="Health score in percentage")
    source: str = Field(default="battery_ai_predictor", description="Data source")

class BatteryPrediction(BaseModel):
    timestamp: float = Field(..., description="Unix timestamp")
    remaining_life_hours: float = Field(..., description="Predicted remaining life in hours")
    remaining_cycles: float = Field(..., description="Predicted remaining cycles")
    degradation_rate: float = Field(..., description="Degradation rate per cycle")
    source: str = Field(default="battery_ai_predictor", description="Data source")

class BatterySpecs(BaseModel):
    nominal_capacity_ah: float
    nominal_voltage: float
    max_cycles: int
    max_temp: float
    min_temp: float
    max_current: float
    chemistry: str
    cell_configuration: str
    rated_power: float

class MonitoringThresholds(BaseModel):
    voltage: dict
    current: dict
    temperature: dict
    health: dict

# Health check endpoint
@app.get("/health")
async def health_check():
    if client is None:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {"status": "healthy", "database": "connected"}

# Store battery monitoring data
@app.post("/api/battery-data")
async def store_battery_data(data: BatteryData):
    try:
        # Add timestamp if not provided
        if not data.timestamp:
            data.timestamp = datetime.now().timestamp()
        
        # Store in MongoDB
        result = await db.battery_data.insert_one(data.dict())
        logger.info(f"Stored battery data with ID: {result.inserted_id}")
        
        # Update AI predictor with new data
        if ai_predictor:
            try:
                # Convert to AI performance format
                ai_data = AIPerformance(
                    timestamp=data.timestamp,
                    pack_voltage=data.pack_voltage,
                    pack_current=data.pack_current,
                    cell_temp=data.cell_temp,
                    # Estimate other fields based on historical data
                    capacity_remaining=95.0,  # Default estimate
                    cycle_count=0,  # Would need to be tracked
                    age_months=6.0,  # Would need to be configured
                    health_score=90.0  # Would need to be calculated
                )
                await ai_predictor.add_performance_data(ai_data)
                
                # Generate prediction every 10 data points
                if len(ai_predictor.performance_history) % 10 == 0:
                    await ai_predictor.predict_battery_life()
                    
            except Exception as e:
                logger.error(f"Error updating AI predictor: {e}")
        
        return {"message": "Battery data stored successfully", "id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error storing battery data: {e}")
        raise HTTPException(status_code=500, detail="Failed to store battery data")

# Store battery performance data
@app.post("/api/battery-performance")
async def store_battery_performance(data: BatteryPerformance):
    try:
        # Add timestamp if not provided
        if not data.timestamp:
            data.timestamp = datetime.now().timestamp()
        
        # Store in MongoDB
        result = await db.battery_performance.insert_one(data.dict())
        logger.info(f"Stored battery performance with ID: {result.inserted_id}")
        
        return {"message": "Battery performance stored successfully", "id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error storing battery performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to store battery performance")

# Store battery prediction data
@app.post("/api/battery-prediction")
async def store_battery_prediction(data: BatteryPrediction):
    try:
        # Add timestamp if not provided
        if not data.timestamp:
            data.timestamp = datetime.now().timestamp()
        
        # Store in MongoDB
        result = await db.battery_predictions.insert_one(data.dict())
        logger.info(f"Stored battery prediction with ID: {result.inserted_id}")
        
        return {"message": "Battery prediction stored successfully", "id": str(result.inserted_id)}
    except Exception as e:
        logger.error(f"Error storing battery prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to store battery prediction")

# Get latest battery data
@app.get("/api/battery-data/latest")
async def get_latest_battery_data():
    try:
        data = await db.battery_data.find_one(
            sort=[("timestamp", -1)]
        )
        if data:
            data["_id"] = str(data["_id"])
            return data
        else:
            raise HTTPException(status_code=404, detail="No battery data found")
    except Exception as e:
        logger.error(f"Error retrieving latest battery data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve battery data")

# Get latest battery performance
@app.get("/api/battery-performance/latest")
async def get_latest_battery_performance():
    try:
        data = await db.battery_performance.find_one(
            sort=[("timestamp", -1)]
        )
        if data:
            data["_id"] = str(data["_id"])
            return data
        else:
            raise HTTPException(status_code=404, detail="No battery performance data found")
    except Exception as e:
        logger.error(f"Error retrieving latest battery performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve battery performance")

# Get latest battery prediction
@app.get("/api/battery-prediction/latest")
async def get_latest_battery_prediction():
    try:
        data = await db.battery_predictions.find_one(
            sort=[("timestamp", -1)]
        )
        if data:
            data["_id"] = str(data["_id"])
            return data
        else:
            raise HTTPException(status_code=404, detail="No battery prediction data found")
    except Exception as e:
        logger.error(f"Error retrieving latest battery prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve battery prediction")

# Generate new AI prediction
@app.post("/api/battery-prediction/generate")
async def generate_battery_prediction():
    if not ai_predictor:
        raise HTTPException(status_code=503, detail="AI predictor not available")
    
    try:
        prediction = await ai_predictor.predict_battery_life()
        return {
            "message": "Prediction generated successfully",
            "prediction": {
                "timestamp": prediction.timestamp,
                "remaining_life_hours": prediction.remaining_life_hours,
                "remaining_cycles": prediction.remaining_cycles,
                "degradation_rate": prediction.degradation_rate,
                "confidence_score": prediction.confidence_score,
                "recommendations": prediction.recommendations or []
            }
        }
    except Exception as e:
        logger.error(f"Error generating prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prediction")

# Get AI predictor status
@app.get("/api/ai-predictor/status")
async def get_ai_predictor_status():
    if not ai_predictor:
        return {"status": "unavailable", "ai_enabled": False}
    
    return {
        "status": "available",
        "ai_enabled": ai_predictor.ai_enabled,
        "data_points": len(ai_predictor.performance_history),
        "predictions_generated": len(ai_predictor.prediction_history)
    }

# Enable/disable AI predictions
@app.post("/api/ai-predictor/enable")
async def enable_ai_predictor(api_key: str = ""):
    if not ai_predictor:
        raise HTTPException(status_code=503, detail="AI predictor not available")
    
    try:
        if api_key:
            ai_predictor.enable_ai(api_key)
            return {"message": "AI predictions enabled with API key"}
        else:
            ai_predictor.disable_ai()
            return {"message": "AI predictions disabled, using analytical mode"}
    except Exception as e:
        logger.error(f"Error configuring AI predictor: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure AI predictor")

# Get battery data history
@app.get("/api/battery-data/history")
async def get_battery_data_history(
    hours: int = 24,
    limit: int = 100
):
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_timestamp = cutoff_time.timestamp()
        
        cursor = db.battery_data.find(
            {"timestamp": {"$gte": cutoff_timestamp}},
            sort=[("timestamp", -1)]
        ).limit(limit)
        
        data = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for item in data:
            item["_id"] = str(item["_id"])
        
        return data
    except Exception as e:
        logger.error(f"Error retrieving battery data history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve battery data history")

# Get battery performance history
@app.get("/api/battery-performance/history")
async def get_battery_performance_history(
    hours: int = 24,
    limit: int = 100
):
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_timestamp = cutoff_time.timestamp()
        
        cursor = db.battery_performance.find(
            {"timestamp": {"$gte": cutoff_timestamp}},
            sort=[("timestamp", -1)]
        ).limit(limit)
        
        data = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for item in data:
            item["_id"] = str(item["_id"])
        
        return data
    except Exception as e:
        logger.error(f"Error retrieving battery performance history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve battery performance history")

# Get battery prediction history
@app.get("/api/battery-prediction/history")
async def get_battery_prediction_history(
    hours: int = 24,
    limit: int = 100
):
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_timestamp = cutoff_time.timestamp()
        
        cursor = db.battery_predictions.find(
            {"timestamp": {"$gte": cutoff_timestamp}},
            sort=[("timestamp", -1)]
        ).limit(limit)
        
        data = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string for JSON serialization
        for item in data:
            item["_id"] = str(item["_id"])
        
        return data
    except Exception as e:
        logger.error(f"Error retrieving battery prediction history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve battery prediction history")

# Get all dashboard data in one call
@app.get("/api/dashboard")
async def get_dashboard_data():
    try:
        # Get latest data from all collections
        latest_battery_data = await db.battery_data.find_one(sort=[("timestamp", -1)])
        latest_performance = await db.battery_performance.find_one(sort=[("timestamp", -1)])
        latest_prediction = await db.battery_predictions.find_one(sort=[("timestamp", -1)])
        
        # Load battery specs from file
        try:
            with open("../frontend/public/battery_specs.json", "r") as f:
                battery_specs = json.load(f)
        except FileNotFoundError:
            battery_specs = {}
        
        dashboard_data = {
            "battery_data": latest_battery_data,
            "performance": latest_performance,
            "prediction": latest_prediction,
            "specs": battery_specs.get("battery_specifications", {}),
            "thresholds": battery_specs.get("monitoring_thresholds", {})
        }
        
        # Convert ObjectIds to strings
        for key in ["battery_data", "performance", "prediction"]:
            if dashboard_data[key]:
                dashboard_data[key]["_id"] = str(dashboard_data[key]["_id"])
        
        return dashboard_data
    except Exception as e:
        logger.error(f"Error retrieving dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

# Cleanup old data (background task)
async def cleanup_old_data():
    """Remove data older than 30 days"""
    try:
        cutoff_time = datetime.now() - timedelta(days=30)
        cutoff_timestamp = cutoff_time.timestamp()
        
        # Clean up old data from all collections
        collections = ["battery_data", "battery_performance", "battery_predictions"]
        for collection_name in collections:
            result = await db[collection_name].delete_many({"timestamp": {"$lt": cutoff_timestamp}})
            logger.info(f"Cleaned up {result.deleted_count} old records from {collection_name}")
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")

# Schedule cleanup task
@app.on_event("startup")
async def startup_event():
    # Create indexes for better query performance
    try:
        await db.battery_data.create_index("timestamp")
        await db.battery_performance.create_index("timestamp")
        await db.battery_predictions.create_index("timestamp")
        logger.info("Database indexes created")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 