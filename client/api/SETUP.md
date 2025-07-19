# Battery Monitoring API Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Setup Script
```bash
python setup_env.py
```

This will:
- Check if all required packages are installed
- Create a `.env` file with all necessary environment variables
- Guide you through setting up your Gemini API key

### 3. Configure Environment Variables

Edit the `.env` file with your actual values:

```bash
# MongoDB Atlas Connection String
MONGODB_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/battery_db?retryWrites=true&w=majority

# Google Gemini AI API Key (Required for AI predictions)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Other settings...
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Start the API Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Gemini API Key Setup

### Why You Need It
The AI predictor uses Google's Gemini AI to provide intelligent battery life predictions. Without an API key, the system will fall back to analytical predictions only.

### How to Get a Gemini API Key

1. **Visit Google AI Studio**
   - Go to: https://makersuite.google.com/app/apikey
   - Sign in with your Google account

2. **Create API Key**
   - Click "Create API Key"
   - Choose "Create API Key in new project" or select existing project
   - Copy the generated API key

3. **Configure in Your System**
   - Add to `.env` file: `GEMINI_API_KEY=your_key_here`
   - Or set environment variable: `export GEMINI_API_KEY=your_key_here`

### API Key Security
- **Never commit your API key to version control**
- **Keep your `.env` file secure**
- **Use environment variables in production**

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONGODB_URI` | MongoDB connection string | Yes | - |
| `GEMINI_API_KEY` | Google Gemini API key | No* | - |
| `DATABASE_NAME` | Database name | No | `battery_db` |
| `API_HOST` | API server host | No | `0.0.0.0` |
| `API_PORT` | API server port | No | `8000` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

*Required for AI predictions, optional for analytical mode

## Testing the Setup

### 1. Check API Health
```bash
curl http://localhost:8000/health
```

### 2. Check AI Predictor Status
```bash
curl http://localhost:8000/api/ai-predictor/status
```

### 3. Test with Sample Data
```bash
curl -X POST http://localhost:8000/api/battery-data \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": 1234567890,
    "pack_voltage": 350.0,
    "pack_current": 50.0,
    "cell_temp": 25.0
  }'
```

## Troubleshooting

### "No Gemini API key found"
- **Solution**: Set `GEMINI_API_KEY` in your `.env` file
- **Alternative**: System will use analytical predictions only

### "Failed to connect to MongoDB"
- **Solution**: Check your `MONGODB_URI` in `.env` file
- **Verify**: Test connection string in MongoDB Compass

### "Module not found" errors
- **Solution**: Run `pip install -r requirements.txt`
- **Verify**: Check Python environment and virtual environment

### API key not working
- **Check**: API key format and validity
- **Verify**: Test key in Google AI Studio
- **Alternative**: Use analytical mode temporarily

## Production Deployment

### Environment Variables
```bash
# Set production environment variables
export MONGODB_URI="your_production_mongodb_uri"
export GEMINI_API_KEY="your_production_api_key"
export LOG_LEVEL="WARNING"
```

### Security Considerations
- Use strong, unique API keys
- Rotate API keys regularly
- Monitor API usage and costs
- Use HTTPS in production
- Implement rate limiting

## API Endpoints

### Core Endpoints
- `POST /api/battery-data` - Store battery readings
- `GET /api/battery-data/latest` - Get latest readings
- `GET /api/battery-data/history` - Get historical data

### AI Prediction Endpoints
- `POST /api/battery-prediction/generate` - Generate new prediction
- `GET /api/battery-prediction/latest` - Get latest prediction
- `GET /api/ai-predictor/status` - Check AI status
- `POST /api/ai-predictor/enable` - Enable/disable AI

### Health Check
- `GET /health` - API health status

## Next Steps

1. **Start the API server**
2. **Configure your QNX monitor** to send data to the backend
3. **Test the complete system** with your battery simulator
4. **Monitor the dashboard** for real-time insights

For more information, see the main [ARCHITECTURE.md](../../ARCHITECTURE.md) file. 