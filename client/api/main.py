from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(
    title="Battery Monitor API",
    description="Real-time battery monitoring and AI prediction system",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the battery monitoring routes
app.include_router(router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "Battery Monitor API",
        "version": "1.0.0",
        "endpoints": {
            "current_data": "/api/battery/current",
            "prediction": "/api/battery/prediction", 
            "status": "/api/battery/status",
            "stats": "/api/battery/stats",
            "history": "/api/battery/history",
            "monitor": "/api/battery/monitor",
            "websocket": "/ws/battery"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "battery-monitor-api"}