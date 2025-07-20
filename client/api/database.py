from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file at project root
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent
env_file = project_root / ".env"
print(f"🔍 Looking for .env file at: {env_file}")
print(f"🔍 .env file exists: {env_file.exists()}")

# Try to load the .env file
load_dotenv(env_file)

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URI", "mongodb://localhost:27017")  # Changed from MONGODB_URL to MONGODB_URI
DATABASE_NAME = os.getenv("DATABASE_NAME", "battery_monitoring")

# Debug: Print what we're connecting to (hide password)
debug_url = MONGODB_URL
if "@" in debug_url:
    # Hide password in debug output
    parts = debug_url.split("@")
    if len(parts) == 2:
        debug_url = "***@" + parts[1]
print(f"🔍 Loading MongoDB URL: {debug_url}")
print(f"🔍 Database name: {DATABASE_NAME}")

# Global MongoDB client
client: Optional[MongoClient] = None

def connect_to_mongo():
    """Connect to MongoDB"""
    global client
    client = MongoClient(MONGODB_URL)
    print(f"✅ Connected to MongoDB: {MONGODB_URL}")
    
    # Create indexes for better query performance
    db = client[DATABASE_NAME]
    collection = db.battery_telemetry
    
    # Create indexes
    collection.create_index([("timestamp", ASCENDING)])
    collection.create_index([("source", ASCENDING)])
    collection.create_index([("received_at", DESCENDING)])
    collection.create_index([("source", ASCENDING), ("timestamp", DESCENDING)])
    
    print("✅ Database indexes created")

def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed")

def get_database():
    """Get database instance"""
    if not client:
        raise Exception("MongoDB client not initialized")
    return client[DATABASE_NAME]

def insert_telemetry(telemetry_data: dict):
    """Insert telemetry data into MongoDB"""
    db = get_database()
    collection = db.battery_telemetry
    
    # Add received_at timestamp if not present
    if "received_at" not in telemetry_data:
        telemetry_data["received_at"] = datetime.utcnow()
    
    result = collection.insert_one(telemetry_data)
    return result.inserted_id

def get_latest_telemetry(source: Optional[str] = None, limit: int = 1):
    """Get latest telemetry data"""
    db = get_database()
    collection = db.battery_telemetry
    
    filter_query = {}
    if source:
        filter_query["source"] = source
    
    cursor = collection.find(filter_query).sort("received_at", DESCENDING).limit(limit)
    return list(cursor)

def get_telemetry_history(source: Optional[str] = None, limit: int = 100, skip: int = 0):
    """Get historical telemetry data"""
    db = get_database()
    collection = db.battery_telemetry
    
    filter_query = {}
    if source:
        filter_query["source"] = source
    
    cursor = collection.find(filter_query).sort("received_at", DESCENDING).skip(skip).limit(limit)
    return list(cursor)

def get_telemetry_stats(source: Optional[str] = None):
    """Get telemetry statistics"""
    db = get_database()
    collection = db.battery_telemetry
    
    filter_query = {}
    if source:
        filter_query["source"] = source
    
    # Get total count
    total_count = collection.count_documents(filter_query)
    
    if total_count == 0:
        return {"total_readings": 0}
    
    # Get latest data
    latest = get_latest_telemetry(source, 1)
    if not latest:
        return {"total_readings": 0}
    
    latest_data = latest[0]
    
    # Calculate statistics using aggregation pipeline
    pipeline = [
        {"$match": filter_query},
        {"$group": {
            "_id": None,
            "avg_voltage": {"$avg": "$pack_voltage"},
            "min_voltage": {"$min": "$pack_voltage"},
            "max_voltage": {"$max": "$pack_voltage"},
            "avg_current": {"$avg": "$pack_current"},
            "min_current": {"$min": "$pack_current"},
            "max_current": {"$max": "$pack_current"},
            "avg_temp": {"$avg": "$cell_temp"},
            "min_temp": {"$min": "$cell_temp"},
            "max_temp": {"$max": "$cell_temp"}
        }}
    ]
    
    stats_result = list(collection.aggregate(pipeline))
    stats = stats_result[0] if stats_result else {}
    
    return {
        "total_readings": total_count,
        "voltage": {
            "current": latest_data["pack_voltage"],
            "min": stats.get("min_voltage", 0),
            "max": stats.get("max_voltage", 0),
            "avg": stats.get("avg_voltage", 0)
        },
        "current": {
            "current": latest_data["pack_current"],
            "min": stats.get("min_current", 0),
            "max": stats.get("max_current", 0),
            "avg": stats.get("avg_current", 0)
        },
        "temperature": {
            "current": latest_data["cell_temp"],
            "min": stats.get("min_temp", 0),
            "max": stats.get("max_temp", 0),
            "avg": stats.get("avg_temp", 0)
        },
        "last_update": latest_data["received_at"].isoformat()
    }

def get_sources():
    """Get list of all data sources"""
    db = get_database()
    collection = db.battery_telemetry
    
    sources = collection.distinct("source")
    return sources 