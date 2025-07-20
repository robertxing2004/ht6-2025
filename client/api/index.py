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
        db = get_database()
        collection = db.battery_telemetry
        # Only find records with specific anomaly types from bat.py
        anomalies = list(collection.find({
            "anomaly_warning": {
                "$exists": True,
                "$ne": None,
                "$regex": "(Low|High) (Voltage|Temperature|Current)"  # Only match these specific patterns
            }
        }).sort("received_at", -1))
        
        print(f"Found {len(anomalies)} valid anomalies in database")
        return {"anomalies": [serialize_document(a) for a in anomalies]}
    except Exception as e:
        print(f"Error fetching anomalies: {e}")
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
            "content": "Gemini API not configured. Please set GEMINI_API_KEY in your .env file.",
            "health_percentage": None,
            "confidence": None
        }
    
    if df.empty:
        return {
            "content": "No data available for analysis",
            "health_percentage": None,
            "confidence": None
        }
    
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
    elif analysis_type == "battery_health":
        prompt = f"""
        Analyze battery health and predict remaining lifespan based on this telemetry data:
        
        Data Summary: {json.dumps(data_summary, indent=2)}
        Source: {source or 'All sources'}
        
        IMPORTANT: Start your response with a JSON block containing the health assessment:
        {{
            "health_percentage": <0-100>,
            "confidence": <0-100>,
            "analysis": "detailed text analysis"
        }}
        
        Then provide a comprehensive battery health analysis including:
        
        1. CURRENT HEALTH ASSESSMENT:
           - Overall battery health percentage (0-100%)
           - Capacity degradation estimate
           - Internal resistance analysis
           - Cell balance assessment
        
        2. PERFORMANCE ANALYSIS:
           - Voltage stability and consistency
           - Temperature impact on performance
           - Charge/discharge efficiency
           - Cycle depth analysis
        
        3. LIFESPAN PREDICTION:
           - Estimated remaining cycles
           - Predicted time to 80% capacity
           - End-of-life estimation
           - Confidence level in prediction
        
        4. DEGRADATION FACTORS:
           - Temperature stress impact
           - Overcharge/overdischarge events
           - High current stress
           - Age-related degradation
        
        5. RECOMMENDATIONS:
           - Optimal charging strategies
           - Temperature management
           - Usage pattern optimization
           - Maintenance schedule
        
        Base your analysis on LiFePO4 battery characteristics and real-world degradation patterns.
        Provide specific percentages, timeframes, and actionable insights.
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
        print(f"🤖 Sending request to Gemini for {analysis_type} analysis...")
        start_time = datetime.now()
        response = gemini_model.generate_content(prompt)
        response_time = (datetime.now() - start_time).total_seconds()
        response_text = response.text
        
        print(f"🤖 Gemini response received in {response_time:.2f}s: {len(response_text)} characters")
        print(f"🤖 Response preview: {response_text[:200]}...")
        
        # Try to extract JSON from the beginning of the response
        import re
        json_match = re.search(r'\{[^{}]*"health_percentage"[^{}]*\}', response_text)
        
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                health_percentage = json_data.get('health_percentage')
                confidence = json_data.get('confidence')
                
                print(f"✅ Extracted health_percentage: {health_percentage}, confidence: {confidence}")
                
                return {
                    "content": response_text,
                    "health_percentage": float(health_percentage) if health_percentage is not None else None,
                    "confidence": float(confidence) if confidence is not None else None
                }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error parsing JSON from Gemini response: {e}")
                print(f"❌ JSON match: {json_match.group()}")
                # Fallback: try to extract percentage from text
                percentage_match = re.search(r'(\d+(?:\.\d+)?)\s*%', response_text)
                if percentage_match:
                    try:
                        health_percentage = float(percentage_match.group(1))
                        print(f"✅ Extracted percentage from text: {health_percentage}%")
                        return {
                            "content": response_text,
                            "health_percentage": health_percentage,
                            "confidence": 70.0  # Default confidence
                        }
                    except ValueError:
                        print(f"❌ Failed to convert percentage: {percentage_match.group(1)}")
                        pass
        
        print(f"❌ No health percentage found in response")
        # If no JSON or percentage found, return full response
        return {
            "content": response_text,
            "health_percentage": None,
            "confidence": None
        }
        
    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")
        return {
            "content": f"Error analyzing data with Gemini: {str(e)}",
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
    """Receive battery telemetry data from QNX systems"""
    try:
        # Debug: Log incoming data
        print(f"🔋 Received battery data: {data.dict()}")
        
        # Validate input data
        if data.pack_voltage < 0 or data.pack_current < -1000 or data.cell_temp < -50 or data.cell_temp > 100:
            raise HTTPException(status_code=400, detail="Invalid battery data values")
        
        # Prepare telemetry data for MongoDB with proper type conversion
        telemetry_entry = {
            "timestamp": float(data.timestamp),
            "pack_voltage": float(data.pack_voltage),
            "pack_current": float(data.pack_current),
            "cell_temp": float(data.cell_temp),
            "source": str(data.source),
            "received_at": datetime.now(timezone.utc)
        }
        
        # Store in MongoDB
        inserted_id = insert_telemetry(telemetry_entry)
        
        print(f"✅ Battery data stored in MongoDB: {telemetry_entry['source']} - ID: {inserted_id}")
        print(f"📊 Data: V={telemetry_entry['pack_voltage']:.2f}V, I={telemetry_entry['pack_current']:.2f}A, T={telemetry_entry['cell_temp']:.1f}°C")
        
        return BatteryResponse(
            message="Data received and stored successfully",
            timestamp=telemetry_entry["received_at"].isoformat(),
            data=data
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Data validation error: {str(e)}")
    except Exception as e:
        print(f"❌ Error processing battery data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
    """Dynamically calculate State of Charge using AI to determine battery type"""
    try:
        if not gemini_model:
            return {
                "soc": None,
                "battery_type": "Unknown",
                "confidence": None,
                "error": "Gemini API not configured"
            }
        
        # Extract values from request body
        voltage = request.voltage
        current = request.current
        temperature = request.temperature
        
        # Create prompt for battery type detection and SoC calculation
        prompt = f"""
        Analyze this battery data and determine the battery type and State of Charge:
        
        Pack Voltage: {voltage}V
        Pack Current: {current}A (if available)
        Temperature: {temperature}°C (if available)
        
        Based on the voltage and any other available data, determine:
        1. Most likely battery chemistry (LiFePO4, Li-ion, LiPo, Lead-acid, etc.)
        2. Estimated cell count and configuration
        3. State of Charge percentage (0-100%)
        4. Confidence level in the calculation (0-100%)
        
        IMPORTANT: Start your response with a JSON block:
        {{
            "battery_type": "chemistry name",
            "cell_count": <estimated number>,
            "cell_voltage": <voltage per cell>,
            "soc_percentage": <0-100>,
            "confidence": <0-100>,
            "voltage_range": {{
                "min": <min voltage>,
                "max": <max voltage>,
                "nominal": <nominal voltage>
            }},
            "reasoning": "brief explanation of the calculation"
        }}
        
        Then provide detailed analysis of how you determined the battery type and SoC.
        """
        
        print(f"🔋 Calculating SoC for {voltage}V pack...")
        start_time = datetime.now()
        response = gemini_model.generate_content(prompt)
        response_time = (datetime.now() - start_time).total_seconds()
        response_text = response.text
        
        print(f"🔋 SoC calculation completed in {response_time:.2f}s")
        print(f"🔋 Gemini response: {response_text[:500]}...")
        
        # Try to extract JSON from the beginning of the response
        import re
        json_match = re.search(r'\{[^{}]*"battery_type"[^{}]*\}', response_text)
        
        if json_match:
            try:
                json_data = json.loads(json_match.group())
                return {
                    "soc": float(json_data.get('soc_percentage', 0)),
                    "battery_type": json_data.get('battery_type', 'Unknown'),
                    "cell_count": json_data.get('cell_count'),
                    "cell_voltage": json_data.get('cell_voltage'),
                    "confidence": float(json_data.get('confidence', 0)),
                    "voltage_range": json_data.get('voltage_range', {}),
                    "reasoning": json_data.get('reasoning', ''),
                    "response_time": response_time,
                    "full_analysis": response_text
                }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ Error parsing JSON from SoC calculation: {e}")
                return {
                    "soc": None,
                    "battery_type": "Unknown",
                    "confidence": None,
                    "error": f"Failed to parse AI response: {e}",
                    "full_analysis": response_text
                }
        else:
            print(f"❌ No JSON found in SoC calculation response")
            return {
                "soc": None,
                "battery_type": "Unknown",
                "confidence": None,
                "error": "No structured data found in AI response",
                "full_analysis": response_text
            }
            
    except Exception as e:
        print(f"❌ Error in SoC calculation: {e}")
        return {
            "soc": None,
            "battery_type": "Unknown",
            "confidence": None,
            "error": f"Calculation error: {str(e)}"
        }

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