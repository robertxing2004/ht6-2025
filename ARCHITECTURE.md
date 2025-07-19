# Battery Monitoring System Architecture

## Overview

This system has been redesigned to move AI prediction logic from QNX to a Python backend, providing better scalability, easier development, and more robust AI integration.

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Battery Data  │───▶│  QNX Monitor     │───▶│  Python Backend │
│   Source        │    │  (Backend Mode)  │    │  (FastAPI)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Data Display   │    │  AI Predictor   │
                       │  & Validation   │    │  (Gemini API)   │
                       └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  MongoDB Atlas  │
                                              │  (Data Storage) │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  React Frontend │
                                              │  (Dashboard)    │
                                              └─────────────────┘
```

## Components

### 1. QNX Components (C++)

#### `battery_monitor_backend.cpp`
- **Purpose**: Simplified QNX monitor that forwards data to backend
- **Features**:
  - Real-time data reception on port 23456
  - Basic validation and threshold checking
  - HTTP POST to Python backend
  - Local display and logging
  - No AI processing (moved to backend)

#### `battery_ai_predictor.cpp` (Legacy)
- **Status**: Deprecated - AI logic moved to Python
- **Use**: Only for reference or if backend is unavailable

### 2. Backend API (Python)

#### `main.py` (FastAPI Server)
- **Purpose**: Main API server with MongoDB integration
- **Endpoints**:
  - `POST /api/battery-data` - Store battery readings
  - `POST /api/battery-performance` - Store performance data
  - `POST /api/battery-prediction` - Store predictions
  - `GET /api/battery-data/latest` - Get latest readings
  - `GET /api/battery-prediction/latest` - Get latest predictions
  - `POST /api/battery-prediction/generate` - Generate new prediction
  - `GET /api/ai-predictor/status` - Check AI status
  - `POST /api/ai-predictor/enable` - Enable/disable AI

#### `battery_ai_predictor.py`
- **Purpose**: AI prediction engine (replaces C++ version)
- **Features**:
  - Google Gemini API integration
  - Analytical fallback mode
  - MongoDB data storage
  - Real-time predictions
  - Confidence scoring
  - Maintenance recommendations

### 3. Frontend (React/TypeScript)

#### Dashboard Components
- Real-time battery monitoring
- AI prediction display
- Historical data visualization
- Alert management

## Data Flow

### 1. Data Collection
```
Battery Source → QNX Monitor → Python Backend → MongoDB
```

### 2. AI Processing
```
MongoDB → AI Predictor → Gemini API → Predictions → MongoDB
```

### 3. Frontend Display
```
MongoDB → FastAPI → React Frontend → User Dashboard
```

## Benefits of New Architecture

### ✅ **Advantages**

1. **Easier AI Integration**
   - Python has better AI/ML libraries
   - Simpler API key management
   - Better error handling for AI calls

2. **Improved Development**
   - Faster iteration cycles
   - Better debugging tools
   - No compilation required for AI changes

3. **Better Scalability**
   - Can handle multiple battery systems
   - Centralized data storage
   - Easier to add new features

4. **Enhanced Reliability**
   - AI failures don't affect QNX monitoring
   - Better error recovery
   - Fallback to analytical mode

5. **Simplified QNX Code**
   - Focus on data collection and validation
   - No complex AI dependencies
   - Easier to maintain and deploy

### ⚠️ **Considerations**

1. **Network Dependency**
   - QNX needs network connection to backend
   - Potential latency in data transmission
   - Need for offline fallback

2. **Resource Usage**
   - Backend requires more resources
   - MongoDB storage costs
   - API rate limiting considerations

## Deployment Options

### Option 1: Local Development
```bash
# Terminal 1: Start Python backend
cd ht6-2025/client/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2: Start QNX monitor
cd ht6-2025/src/qnx
make battery_monitor_backend
./battery_monitor_backend --backend http://localhost:8000

# Terminal 3: Start frontend
cd ht6-2025/client/frontend
npm install
npm run dev
```

### Option 2: Production Deployment
```bash
# Deploy backend to cloud (AWS, Azure, etc.)
# Configure MongoDB Atlas
# Deploy frontend to CDN
# Configure QNX for production backend URL
```

## Configuration

### Environment Variables
```bash
# Backend (.env)
MONGODB_URI=mongodb+srv://...
GEMINI_API_KEY=your_gemini_api_key
BACKEND_URL=http://localhost:8000

# QNX Monitor
BACKEND_URL=http://your-backend-url:8000
```

### Battery Specifications
```json
{
  "battery_specifications": {
    "nominal_capacity_ah": 100.0,
    "nominal_voltage": 355.2,
    "max_cycles": 1000,
    "chemistry": "LiFePO4",
    "cell_configuration": "96S72P"
  }
}
```

## Migration Guide

### From Old Architecture
1. **Stop old QNX AI predictor**
2. **Deploy new backend**
3. **Update QNX monitor to backend mode**
4. **Configure API keys**
5. **Test data flow**

### Fallback Strategy
- QNX continues monitoring even if backend is down
- Local logging and display still work
- AI predictions resume when backend is available

## Monitoring and Maintenance

### Health Checks
- Backend: `GET /health`
- AI Predictor: `GET /api/ai-predictor/status`
- Database: MongoDB connection status

### Logging
- QNX: `battery_monitor_backend.log`
- Backend: FastAPI logs
- AI: Prediction logs in MongoDB

### Performance Metrics
- Data collection rate
- AI prediction accuracy
- API response times
- Database performance

## Future Enhancements

1. **Machine Learning Models**
   - Train custom models on historical data
   - Improve prediction accuracy
   - Add anomaly detection

2. **Real-time Analytics**
   - Live performance dashboards
   - Predictive maintenance alerts
   - Trend analysis

3. **Multi-battery Support**
   - Fleet management
   - Comparative analysis
   - Centralized monitoring

4. **Edge Computing**
   - Local AI processing for critical systems
   - Hybrid cloud/edge architecture
   - Offline capabilities 