# Battery Monitoring API

A FastAPI backend with MongoDB Atlas integration for storing and retrieving battery data from QNX monitoring and AI prediction processes.

## Features

- **FastAPI Backend**: High-performance async API with automatic documentation
- **MongoDB Atlas Integration**: Cloud database for scalable data storage
- **Real-time Data Collection**: Receives data from QNX C++ processes
- **RESTful API**: Complete CRUD operations for battery data
- **Data Validation**: Pydantic models ensure data integrity
- **CORS Support**: Frontend integration ready
- **Automatic Indexing**: Optimized database queries
- **Data Cleanup**: Automatic removal of old data

## Architecture

```
QNX Processes (C++) → Data Collector (Python) → FastAPI Backend → MongoDB Atlas
                                                      ↓
                                              React Frontend
```

## Setup

### 1. MongoDB Atlas Setup

1. Create a MongoDB Atlas account at [mongodb.com](https://mongodb.com)
2. Create a new cluster (free tier available)
3. Create a database user with read/write permissions
4. Get your connection string
5. Create a `.env` file with your MongoDB URI:

```bash
MONGODB_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/battery_db?retryWrites=true&w=majority
```

### 2. Install Dependencies

```bash
cd client/api
pip install -r requirements.txt
```

### 3. Start the Backend

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### 4. Start the Data Collector

```bash
python data_collector.py
```

## API Endpoints

### Health Check
- `GET /health` - Check API and database status

### Battery Data
- `POST /api/battery-data` - Store battery monitoring data
- `GET /api/battery-data/latest` - Get latest battery data
- `GET /api/battery-data/history?hours=24&limit=100` - Get historical data

### Battery Performance
- `POST /api/battery-performance` - Store performance data
- `GET /api/battery-performance/latest` - Get latest performance data
- `GET /api/battery-performance/history?hours=24&limit=100` - Get historical data

### Battery Predictions
- `POST /api/battery-prediction` - Store AI prediction data
- `GET /api/battery-prediction/latest` - Get latest prediction
- `GET /api/battery-prediction/history?hours=24&limit=100` - Get historical data

### Dashboard
- `GET /api/dashboard` - Get all latest data for frontend

## Data Models

### BatteryData
```json
{
  "timestamp": 1640995200.0,
  "pack_voltage": 355.2,
  "pack_current": 50.0,
  "cell_temp": 25.5,
  "source": "battery_monitor"
}
```

### BatteryPerformance
```json
{
  "timestamp": 1640995200.0,
  "pack_voltage": 355.2,
  "pack_current": 50.0,
  "cell_temp": 25.5,
  "capacity_remaining": 85.5,
  "cycle_count": 150,
  "age_months": 6.2,
  "health_score": 92.3,
  "source": "battery_ai_predictor"
}
```

### BatteryPrediction
```json
{
  "timestamp": 1640995200.0,
  "remaining_life_hours": 5000.0,
  "remaining_cycles": 850.0,
  "degradation_rate": 0.12,
  "source": "battery_ai_predictor"
}
```

## Integration with QNX Processes

### 1. Battery Monitor (battery_monitor.cpp)
The data collector listens on port 23456 for binary data:
```cpp
struct BatteryData {
    float timestamp;
    float pack_voltage;
    float pack_current;
    float cell_temp;
};
```

### 2. AI Predictor (battery_ai_predictor.cpp)
The data collector listens on port 23457 for JSON data:
```json
{
  "timestamp": 1640995200.0,
  "remaining_life_hours": 5000.0,
  "remaining_cycles": 850.0,
  "degradation_rate": 0.12
}
```

## Database Collections

- `battery_data` - Real-time monitoring data
- `battery_performance` - Performance metrics
- `battery_predictions` - AI predictions

## Frontend Integration

Update your React frontend to fetch data from the API:

```javascript
// Get all dashboard data
const response = await fetch('http://localhost:8000/api/dashboard');
const data = await response.json();

// Get latest battery data
const batteryData = await fetch('http://localhost:8000/api/battery-data/latest');
```

## Development

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

### Logs
- API logs: Console output
- Data collector logs: `data_collector.log`

### Environment Variables
- `MONGODB_URI` - MongoDB Atlas connection string
- `DATABASE_NAME` - Database name (default: battery_db)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)

## Production Deployment

1. Set up environment variables
2. Use a production ASGI server (Gunicorn + Uvicorn)
3. Set up MongoDB Atlas with proper security
4. Configure CORS for your production domain
5. Set up monitoring and logging

## Troubleshooting

### Connection Issues
- Verify MongoDB Atlas connection string
- Check network connectivity
- Ensure database user has proper permissions

### Data Collection Issues
- Verify QNX processes are running
- Check port availability (23456, 23457)
- Review data collector logs

### Performance Issues
- Monitor MongoDB Atlas usage
- Check API response times
- Review database indexes 