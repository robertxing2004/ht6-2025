from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import google.generativeai as genai
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
import io

# Import database components
from database import (
    connect_to_mongo, 
    close_mongo_connection, 
    insert_telemetry, 
    get_latest_telemetry, 
    get_telemetry_history, 
    get_telemetry_stats,
    get_sources
)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None

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

class VisualizationRequest(BaseModel):
    source: Optional[str] = None
    time_range_hours: Optional[int] = 24
    analysis_type: str = Field(default="performance", description="Type of analysis: performance, trends, anomalies, or summary")

# Helper functions for data analysis and visualization
def prepare_telemetry_dataframe(telemetry_data: List[Dict]) -> pd.DataFrame:
    """Convert telemetry data to pandas DataFrame for analysis"""
    if not telemetry_data:
        return pd.DataFrame()
    
    # Debug: Check the first record
    if telemetry_data:
        first_record = telemetry_data[0]
        print(f"DEBUG: First record keys: {list(first_record.keys())}")
        print(f"DEBUG: received_at type: {type(first_record.get('received_at'))}")
        print(f"DEBUG: received_at value: {first_record.get('received_at')}")
        print(f"DEBUG: timestamp type: {type(first_record.get('timestamp'))}")
        print(f"DEBUG: timestamp value: {first_record.get('timestamp')}")
    
    df = pd.DataFrame(telemetry_data)
    
    # Handle received_at - it might be a dict from MongoDB json_util
    if 'received_at' in df.columns:
        # Check if it's a dict (MongoDB datetime object)
        if df['received_at'].dtype == 'object':
            # Convert dict datetime objects to strings first
            df['received_at'] = df['received_at'].apply(lambda x: 
                x.get('$date') if isinstance(x, dict) and '$date' in x else x
            )
        df['received_at'] = pd.to_datetime(df['received_at'])
    
    # Handle timestamp
    if 'timestamp' in df.columns:
        if df['timestamp'].dtype == 'object':
            # Convert dict timestamp objects to strings first
            df['timestamp'] = df['timestamp'].apply(lambda x: 
                x.get('$date') if isinstance(x, dict) and '$date' in x else x
            )
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df.sort_values('received_at')

def create_performance_visualization(df: pd.DataFrame, source: str = None) -> str:
    """Create a comprehensive performance visualization using Plotly"""
    if df.empty:
        return "No data available for visualization"
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Voltage Over Time', 'Current Over Time', 'Temperature Over Time'),
        vertical_spacing=0.08,
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]]
    )
    
    # Voltage plot
    fig.add_trace(
        go.Scatter(x=df['received_at'], y=df['pack_voltage'], 
                  mode='lines+markers', name='Voltage', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Current plot
    fig.add_trace(
        go.Scatter(x=df['received_at'], y=df['pack_current'], 
                  mode='lines+markers', name='Current', line=dict(color='red')),
        row=2, col=1
    )
    
    # Temperature plot
    fig.add_trace(
        go.Scatter(x=df['received_at'], y=df['cell_temp'], 
                  mode='lines+markers', name='Temperature', line=dict(color='orange')),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=f'Battery Module Performance - {source or "All Sources"}',
        height=800,
        showlegend=True,
        xaxis3_title="Time",
        yaxis_title="Voltage (V)",
        yaxis2_title="Current (A)",
        yaxis3_title="Temperature (°C)"
    )
    
    # Convert to base64 for embedding
    img_bytes = fig.to_image(format="png", width=1200, height=800)
    img_base64 = base64.b64encode(img_bytes).decode()
    
    return img_base64

def analyze_with_gemini(df: pd.DataFrame, analysis_type: str, source: str = None) -> str:
    """Use Gemini AI to analyze the telemetry data"""
    if not gemini_model:
        return "Gemini API not configured. Please set GEMINI_API_KEY in your .env file."
    
    if df.empty:
        return "No data available for analysis"
    
    # Prepare data summary for Gemini
    data_summary = {
        "total_readings": len(df),
        "time_range": f"{df['received_at'].min()} to {df['received_at'].max()}",
        "voltage_stats": {
            "mean": df['pack_voltage'].mean(),
            "min": df['pack_voltage'].min(),
            "max": df['pack_voltage'].max(),
            "std": df['pack_voltage'].std()
        },
        "current_stats": {
            "mean": df['pack_current'].mean(),
            "min": df['pack_current'].min(),
            "max": df['pack_current'].max(),
            "std": df['pack_current'].std()
        },
        "temperature_stats": {
            "mean": df['cell_temp'].mean(),
            "min": df['cell_temp'].min(),
            "max": df['cell_temp'].max(),
            "std": df['cell_temp'].std()
        }
    }
    
    # Create prompt based on analysis type
    if analysis_type == "performance":
        prompt = f"""
        Analyze this battery module performance data and provide insights:
        
        Data Summary: {json.dumps(data_summary, indent=2)}
        Source: {source or 'All sources'}
        
        Please provide:
        1. Overall performance assessment
        2. Key trends and patterns
        3. Potential issues or concerns
        4. Recommendations for optimization
        5. Performance rating (1-10)
        
        Focus on battery health, efficiency, and operational insights.
        """
    elif analysis_type == "trends":
        prompt = f"""
        Analyze trends in this battery module data:
        
        Data Summary: {json.dumps(data_summary, indent=2)}
        Source: {source or 'All sources'}
        
        Please identify:
        1. Voltage trends over time
        2. Current consumption patterns
        3. Temperature variations
        4. Seasonal or time-based patterns
        5. Correlation between voltage, current, and temperature
        
        Provide specific trend analysis with actionable insights.
        """
    elif analysis_type == "anomalies":
        prompt = f"""
        Detect anomalies in this battery module data:
        
        Data Summary: {json.dumps(data_summary, indent=2)}
        Source: {source or 'All sources'}
        
        Please identify:
        1. Unusual voltage spikes or drops
        2. Abnormal current consumption
        3. Temperature anomalies
        4. Potential system issues
        5. Data quality concerns
        
        Flag any readings that seem suspicious or indicate problems.
        """
    else:  # summary
        prompt = f"""
        Provide a comprehensive summary of this battery module data:
        
        Data Summary: {json.dumps(data_summary, indent=2)}
        Source: {source or 'All sources'}
        
        Please provide:
        1. Executive summary
        2. Key metrics overview
        3. System health assessment
        4. Operational status
        5. Next steps or recommendations
        """
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error analyzing data with Gemini: {str(e)}"

# MongoDB connection events
@app.on_event("startup")
async def startup_event():
    connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    close_mongo_connection()

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
    try:
        # Get latest telemetry to check database connectivity
        latest = get_latest_telemetry(limit=1)
        total_readings = len(latest) if latest else 0
        last_update = latest[0]["received_at"].isoformat() if latest else None
        
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "total_readings": total_readings,
            "last_update": last_update,
            "database": "MongoDB"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "database": "MongoDB"
        }

@app.post("/api/battery-data", response_model=BatteryResponse, tags=["Battery"])
async def receive_battery_data(data: BatteryData):
    """Receive battery telemetry data from QNX systems"""
    try:
        # Prepare telemetry data for MongoDB
        telemetry_entry = {
            "timestamp": data.timestamp,
            "pack_voltage": data.pack_voltage,
            "pack_current": data.pack_current,
            "cell_temp": data.cell_temp,
            "source": data.source,
            "received_at": datetime.utcnow()
        }
        
        # Store in MongoDB
        inserted_id = insert_telemetry(telemetry_entry)
        
        print(f"✅ Battery data stored in MongoDB: {telemetry_entry['source']} - ID: {inserted_id}")
        
        return BatteryResponse(
            message="Data received and stored successfully",
            timestamp=telemetry_entry["received_at"].isoformat(),
            data=data
        )
        
    except Exception as e:
        print(f"❌ Error processing battery data: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.get("/api/battery/current", tags=["Battery"])
async def get_current_battery_data(source: Optional[str] = None):
    """Get the most recent battery data"""
    try:
        latest = get_latest_telemetry(source=source, limit=1)
        
        if not latest:
            raise HTTPException(status_code=404, detail="No battery data available")
        
        return {
            "current_data": latest[0],
            "total_readings": len(latest)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

@app.get("/api/battery/history", tags=["Battery"])
async def get_battery_history(limit: int = 100, source: Optional[str] = None, skip: int = 0):
    """Get historical battery data"""
    try:
        history = get_telemetry_history(source=source, limit=limit, skip=skip)
        
        return {
            "history": history,
            "total_readings": len(history),
            "returned_count": len(history),
            "source": source if source else "all"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@app.get("/api/battery/stats", tags=["Battery"])
async def get_battery_stats(source: Optional[str] = None):
    """Get battery statistics"""
    try:
        stats = get_telemetry_stats(source=source)
        
        if stats["total_readings"] == 0:
            raise HTTPException(status_code=404, detail="No battery data available")
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

@app.get("/api/battery/sources", tags=["Battery"])
async def get_battery_sources():
    """Get list of all data sources"""
    try:
        sources = get_sources()
        return {
            "sources": sources,
            "count": len(sources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sources: {str(e)}")

@app.post("/api/battery/visualize", tags=["Battery"])
async def generate_battery_visualization(request: VisualizationRequest):
    """Generate AI-powered battery performance visualization and analysis"""
    try:
        # Get telemetry data
        if request.time_range_hours:
            # Calculate time range (simplified - you might want to add proper time filtering)
            limit = request.time_range_hours * 12  # Assuming 5-second intervals
        else:
            limit = 1000  # Default to last 1000 readings
        
        telemetry_data = get_telemetry_history(
            source=request.source, 
            limit=limit
        )
        
        if not telemetry_data:
            raise HTTPException(status_code=404, detail="No telemetry data available for visualization")
        
        # Prepare data for analysis
        df = prepare_telemetry_dataframe(telemetry_data)
        
        # Generate visualization
        visualization_base64 = create_performance_visualization(df, request.source)
        
        # Generate AI analysis
        ai_analysis = analyze_with_gemini(df, request.analysis_type, request.source)
        
        # Prepare response
        response_data = {
            "visualization": {
                "type": "image/png",
                "data": visualization_base64,
                "description": f"Performance visualization for {request.source or 'all sources'}"
            },
            "analysis": {
                "type": request.analysis_type,
                "content": ai_analysis,
                "source": request.source or "all sources",
                "data_points": len(df)
            },
            "metadata": {
                "time_range": f"{df['received_at'].min()} to {df['received_at'].max()}",
                "total_readings": len(df),
                "sources_included": df['source'].unique().tolist() if 'source' in df.columns else []
            }
        }
        
        return response_data
        
    except Exception as e:
        print(f"❌ Error generating visualization: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating visualization: {str(e)}")

@app.get("/api/battery/visualize/quick", tags=["Battery"])
async def quick_visualization(source: Optional[str] = None):
    """Quick visualization endpoint for the latest data"""
    try:
        # Get recent data
        telemetry_data = get_telemetry_history(source=source, limit=100)
        
        if not telemetry_data:
            raise HTTPException(status_code=404, detail="No telemetry data available")
        
        # Prepare data
        df = prepare_telemetry_dataframe(telemetry_data)
        
        # Generate visualization
        visualization_base64 = create_performance_visualization(df, source)
        
        # Quick AI summary
        ai_summary = analyze_with_gemini(df, "summary", source)
        
        return {
            "visualization": visualization_base64,
            "summary": ai_summary,
            "data_points": len(df),
            "source": source or "all sources"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quick visualization: {str(e)}")

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