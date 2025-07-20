from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
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
    get_sources,
    get_database,
    serialize_document
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

# Create router for anomalies
anomaly_router = APIRouter()

@anomaly_router.get("/api/battery/anomalies")
async def get_anomalies():
    """Get battery telemetry records with specific anomaly types (matching bat.py)"""
    try:
        print("🔍 Fetching anomalies from database...")
        db = get_database()
        collection = db.battery_telemetry
        
        # Debug: Print collection info
        print(f"📊 Collection name: {collection.name}")
        print(f"📊 Total documents: {collection.count_documents({})}")
        
        # Only find records with specific anomaly types from bat.py
        query = {
            "anomaly_warning": {
                "$exists": True,
                "$ne": None,
                "$regex": "(Low|High) (Voltage|Temperature|Current)"  # Only match these specific patterns
            }
        }
        
        # Debug: Print query
        print(f"🔍 Query: {query}")
        
        # Execute query
        anomalies = list(collection.find(query).sort("received_at", -1))
        
        # Debug: Print results
        print(f"✅ Found {len(anomalies)} valid anomalies")
        if anomalies:
            print("📝 Sample anomaly:", {
                "source": anomalies[0].get("source"),
                "warning": anomalies[0].get("anomaly_warning"),
                "voltage": anomalies[0].get("pack_voltage"),
                "current": anomalies[0].get("pack_current"),
                "temp": anomalies[0].get("cell_temp")
            })
        
        # Serialize and return
        serialized = [serialize_document(a) for a in anomalies]
        print(f"📤 Returning {len(serialized)} serialized anomalies")
        return {"anomalies": serialized}
    except Exception as e:
        print(f"❌ Error fetching anomalies: {e}")
        return {"anomalies": [], "error": str(e)}

# Include the router in the app
app.include_router(anomaly_router)

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
    analysis_type: str = Field(default="performance", description="Type of analysis: performance, trends, anomalies, summary, or battery_health")

class SoCRequest(BaseModel):
    voltage: float
    current: Optional[float] = None
    temperature: Optional[float] = None

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
        # Use flexible parsing for mixed ISO8601 formats
        try:
            df['received_at'] = pd.to_datetime(df['received_at'], format='mixed', errors='coerce', utc=True)
        except TypeError:
            # Fallback for older pandas without 'mixed'
            df['received_at'] = pd.to_datetime(df['received_at'], errors='coerce', utc=True)
    
    # Handle timestamp - it's a float (Unix timestamp), not a date string
    if 'timestamp' in df.columns:
        # Convert Unix timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
    
    return df.sort_values('received_at')

def create_performance_visualization(df: pd.DataFrame, source: str = None) -> str:
    """Create a comprehensive performance visualization using Plotly"""
    if df.empty:
        return "No data available for visualization"
    
    try:
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
        
        # Try to convert to image, with fallback to HTML
        try:
            img_bytes = fig.to_image(format="png", width=1200, height=800)
            img_base64 = base64.b64encode(img_bytes).decode()
            return img_base64
        except Exception as img_error:
            print(f"❌ Image generation failed: {img_error}")
            # Fallback: return HTML representation
            html_content = fig.to_html(include_plotlyjs=False, full_html=False)
            # Convert HTML to base64 for consistency
            html_bytes = html_content.encode('utf-8')
            html_base64 = base64.b64encode(html_bytes).decode()
            return f"html:{html_base64}"
            
    except Exception as e:
        print(f"❌ Visualization creation failed: {e}")
        return f"Error creating visualization: {str(e)}"

def analyze_with_gemini(df: pd.DataFrame, analysis_type: str, source: str = None) -> dict:
    """Use Gemini AI to analyze the telemetry data"""
    if not gemini_model:
        return {
            "content": "Gemini API not configured",
            "health_percentage": None,
            "confidence": None
        }
    
    if df.empty:
        return {
            "content": "No data available",
            "health_percentage": None,
            "confidence": None
        }
    
    # Prepare data summary for Gemini
    data_summary = {
        "total_readings": len(df),
        "voltage": {"mean": df['pack_voltage'].mean(), "min": df['pack_voltage'].min(), "max": df['pack_voltage'].max()},
        "current": {"mean": df['pack_current'].mean(), "min": df['pack_current'].min(), "max": df['pack_current'].max()},
        "temp": {"mean": df['cell_temp'].mean(), "min": df['cell_temp'].min(), "max": df['cell_temp'].max()}
    }
    
    # Create concise prompts based on analysis type
    if analysis_type == "performance":
        prompt = f"""
        Battery performance analysis for {source or 'all sources'}:
        {json.dumps(data_summary, indent=2)}
        
        Provide brief assessment of:
        1. Overall performance (1-5 stars)
        2. Key issues (if any)
        3. Quick recommendations
        
        Keep response under 100 words.
        """
    elif analysis_type == "battery_health":
        prompt = f"""
        Analyze this battery data and provide a brief, clear assessment:
        {json.dumps(data_summary, indent=2)}
        
        Provide a concise analysis in 3-4 short paragraphs:
        1. Current Status: How is the battery performing right now?
        2. Key Observations: What stands out in the voltage, current, and temperature?
        3. Recommendations: Any specific actions needed?
        
        Keep each paragraph to 2-3 sentences. Use simple, direct language.
        Focus on practical insights that a technician would find useful.
        """
    else:  # summary
        prompt = f"""
        Quick battery summary for {source or 'all sources'}:
        {json.dumps(data_summary, indent=2)}
        
        Provide 2-3 sentence overview focusing on critical metrics and issues.
        """
    
    try:
        print(f"🤖 Requesting {analysis_type} analysis...")
        start_time = datetime.now()
        
        # Set generation config for shorter responses
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,  # More focused responses
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 150  # Limit response length
            }
        )
        
        response_time = (datetime.now() - start_time).total_seconds()
        response_text = response.text
        
        print(f"🤖 Response received in {response_time:.2f}s")
        
        # Try to extract JSON health data if present
        import re
        json_match = re.search(r'\{[^{}]*"health_percentage"[^{}]*\}', response_text)
        
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                return {
                    "content": response_text,
                    "health_percentage": float(json_data.get('health_percentage', 0)),
                    "confidence": float(json_data.get('confidence', 0))
                }
            except:
                # Fallback to percentage extraction
                percentage_match = re.search(r'(\d+(?:\.\d+)?)\s*%', response_text)
                if percentage_match:
                    return {
                        "content": response_text,
                        "health_percentage": float(percentage_match.group(1)),
                        "confidence": 70.0
                    }
        
        return {
            "content": response_text,
            "health_percentage": None,
            "confidence": None
        }
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return {
            "content": "Analysis failed",
            "health_percentage": None,
            "confidence": None
        }

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
        print(f"❌ Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "database": "MongoDB"
        }

@app.post("/api/battery-data", response_model=BatteryResponse, tags=["Battery"])
async def receive_battery_data(data: BatteryData):
    """Receive and store battery telemetry data"""
    try:
        # Check for anomalies based on thresholds from bat.py
        anomaly_warning = None
        if data.pack_voltage <= 50:
            anomaly_warning = f"Low Voltage ({data.pack_voltage}V)"
        elif data.pack_voltage >= 500:
            anomaly_warning = f"High Voltage ({data.pack_voltage}V)"
        elif data.pack_current <= 0:
            anomaly_warning = f"Low Current ({data.pack_current}A)"
        elif data.pack_current >= 100:
            anomaly_warning = f"High Current ({data.pack_current}A)"
        elif data.cell_temp <= -20:
            anomaly_warning = f"Low Temperature ({data.cell_temp}°C)"
        elif data.cell_temp >= 60:
            anomaly_warning = f"High Temperature ({data.cell_temp}°C)"

        # Prepare data for storage
        telemetry_data = {
            "timestamp": data.timestamp,
            "pack_voltage": data.pack_voltage,
            "pack_current": data.pack_current,
            "cell_temp": data.cell_temp,
            "source": data.source,
            "received_at": datetime.now(timezone.utc),
            "anomaly_warning": anomaly_warning
        }

        # Store in database
        insert_telemetry(telemetry_data)

        # Debug log
        if anomaly_warning:
            print(f"⚠️ Anomaly detected: {anomaly_warning} for {data.source}")

        return {
            "message": "Data received successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
    except Exception as e:
        print(f"❌ Error processing battery data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Error retrieving current battery data: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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
        print(f"🔍 Starting visualization generation for {request.analysis_type}")
        print(f"🔍 Request details: source={request.source}, time_range={request.time_range_hours}h")
        
        # Get telemetry data
        if request.time_range_hours:
            # Calculate time range (simplified - you might want to add proper time filtering)
            limit = request.time_range_hours * 12  # Assuming 5-second intervals
        else:
            limit = 1000  # Default to last 1000 readings
        
        print(f"🔍 Fetching {limit} telemetry records...")
        start_time = datetime.now()
        telemetry_data = get_telemetry_history(
            source=request.source, 
            limit=limit
        )
        fetch_time = (datetime.now() - start_time).total_seconds()
        print(f"🔍 Data fetch completed in {fetch_time:.2f}s, got {len(telemetry_data)} records")
        
        if not telemetry_data:
            raise HTTPException(status_code=404, detail="No telemetry data available for visualization")
        
        print(f"🔍 Preparing DataFrame with {len(telemetry_data)} records...")
        start_time = datetime.now()
        # Prepare data for analysis
        df = prepare_telemetry_dataframe(telemetry_data)
        df_time = (datetime.now() - start_time).total_seconds()
        print(f"🔍 DataFrame prepared in {df_time:.2f}s: {len(df)} rows, columns: {list(df.columns)}")
        
        # Generate visualization
        print(f"🔍 Generating visualization...")
        start_time = datetime.now()
        visualization_base64 = create_performance_visualization(df, request.source)
        viz_time = (datetime.now() - start_time).total_seconds()
        print(f"🔍 Visualization generated in {viz_time:.2f}s")
        
        # Generate AI analysis
        print(f"🔍 Generating AI analysis for {request.analysis_type}...")
        start_time = datetime.now()
        ai_analysis = analyze_with_gemini(df, request.analysis_type, request.source)
        ai_time = (datetime.now() - start_time).total_seconds()
        print(f"🔍 AI analysis completed in {ai_time:.2f}s")
        
        # Prepare response
        response_data = {
            "visualization": {
                "type": "image/png",
                "data": visualization_base64,
                "description": f"Performance visualization for {request.source or 'all sources'}"
            },
            "analysis": {
                "type": request.analysis_type,
                "content": ai_analysis.get("content", "Analysis unavailable"),
                "source": request.source or "all sources",
                "data_points": len(df),
                "health_percentage": ai_analysis.get("health_percentage"),
                "confidence": ai_analysis.get("confidence")
            },
            "metadata": {
                "time_range": f"{df['received_at'].min()} to {df['received_at'].max()}",
                "total_readings": len(df),
                "sources_included": df['source'].unique().tolist() if 'source' in df.columns else []
            }
        }
        
        total_time = fetch_time + df_time + viz_time + ai_time
        print(f"✅ Visualization generation completed successfully in {total_time:.2f}s total")
        return response_data
        
    except Exception as e:
        print(f"❌ Error generating visualization: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
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

@app.post("/api/battery/test-data", tags=["Battery"])
async def send_test_data():
    """Send test battery data for debugging"""
    import time
    
    test_data = BatteryData(
        timestamp=time.time(),
        pack_voltage=48.5 + (time.time() % 10),  # Varying voltage
        pack_current=-15.2 + (time.time() % 5),  # Varying current
        cell_temp=25.0 + (time.time() % 3),      # Varying temperature
        source="test_simulator"
    )
    
    # Use the existing endpoint logic
    return await receive_battery_data(test_data)

@app.get("/api/battery/test-gemini", tags=["Battery"])
async def test_gemini():
    """Test Gemini API connection and response"""
    try:
        if not gemini_model:
            return {
                "status": "error",
                "message": "Gemini API not configured. Please set GEMINI_API_KEY in your .env file."
            }
        
        # Simple test prompt
        test_prompt = """
        Analyze this simple battery data and provide a health percentage:
        
        Data Summary: {
            "total_readings": 100,
            "voltage_stats": {"mean": 48.5, "min": 45.0, "max": 52.0},
            "current_stats": {"mean": -15.2, "min": -20.0, "max": -10.0},
            "temperature_stats": {"mean": 25.0, "min": 20.0, "max": 30.0}
        }
        
        IMPORTANT: Start your response with a JSON block:
        {
            "health_percentage": <0-100>,
            "confidence": <0-100>,
            "analysis": "brief analysis"
        }
        """
        
        print("🧪 Testing Gemini API...")
        start_time = datetime.now()
        response = gemini_model.generate_content(test_prompt)
        response_time = (datetime.now() - start_time).total_seconds()
        response_text = response.text
        
        print(f"🧪 Test response received in {response_time:.2f}s: {response_text[:500]}...")
        
        # Try to extract JSON
        import re
        json_match = re.search(r'\{[^{}]*"health_percentage"[^{}]*\}', response_text)
        
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                return {
                    "status": "success",
                    "response_time": response_time,
                    "health_percentage": json_data.get('health_percentage'),
                    "confidence": json_data.get('confidence'),
                    "response_preview": response_text[:200] + "..."
                }
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": f"Failed to parse JSON: {e}",
                    "response": response_text
                }
        else:
            return {
                "status": "error",
                "message": "No JSON found in response",
                "response": response_text
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Gemini API error: {str(e)}"
        }

@app.get("/api/battery/test-quick", tags=["Battery"])
async def test_quick_response():
    """Test quick response without AI to check if backend is responsive"""
    return {
        "status": "success",
        "message": "Backend is responsive",
        "timestamp": datetime.now().isoformat(),
        "response_time": "immediate"
    }

@app.post("/api/battery/calculate-soc", tags=["Battery"])
async def calculate_soc_dynamic(request: SoCRequest):
    """Dynamically calculate State of Charge using AI"""
    try:
        if not gemini_model:
            return {"soc": None, "error": "AI not configured"}
        
        prompt = f"""
        Battery data:
        - Voltage: {request.voltage}V
        - Current: {request.current}A
        - Temperature: {request.temperature}°C

        Return only in format:
        {{
            "battery_type": "<type>",
            "cell_count": <number>,
            "soc": <0-100>,
            "confidence": <0-100>
        }}
        """
        
        response = gemini_model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 100
            }
        )
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[^{}]*"battery_type"[^{}]*\}', response.text)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                return {
                    "soc": float(data.get('soc', 0)),
                    "battery_type": data.get('battery_type', 'Unknown'),
                    "cell_count": data.get('cell_count'),
                    "confidence": float(data.get('confidence', 0))
                }
            except:
                return {"soc": None, "error": "Invalid response format"}
        else:
            return {"soc": None, "error": "No data found"}
            
    except Exception as e:
        return {"soc": None, "error": str(e)}

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