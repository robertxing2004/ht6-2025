import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import os
from pymongo import MongoClient
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BatteryPerformance:
    timestamp: float
    pack_voltage: float
    pack_current: float
    cell_temp: float
    capacity_remaining: float = 100.0
    cycle_count: int = 0
    age_months: float = 0.0
    health_score: float = 100.0

@dataclass
class BatteryPrediction:
    timestamp: float
    remaining_life_hours: float
    remaining_cycles: float
    degradation_rate: float
    confidence_score: float = 0.0
    recommendations: List[str] = None

@dataclass
class BatterySpecs:
    nominal_capacity_ah: float = 100.0
    nominal_voltage: float = 355.2
    max_cycles: int = 1000
    max_temp: float = 60.0
    min_temp: float = -20.0
    max_current: float = 500.0
    chemistry: str = "LiFePO4"
    cell_configuration: str = "96S72P"

class BatteryAIPredictor:
    def __init__(self, gemini_api_key: str = "", mongo_uri: str = ""):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.ai_enabled = bool(self.gemini_api_key)
        
        # MongoDB connection
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "")
        self.db = None
        if self.mongo_uri:
            try:
                self.client = AsyncIOMotorClient(self.mongo_uri)
                self.db = self.client.battery_db
                logger.info("Connected to MongoDB for AI predictor")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
        
        # Battery specifications
        self.specs = self.load_battery_specs()
        
        # Performance history (in-memory cache)
        self.performance_history: List[BatteryPerformance] = []
        self.prediction_history: List[BatteryPrediction] = []
        
        logger.info(f"Battery AI Predictor initialized. AI enabled: {self.ai_enabled}")
    
    def load_battery_specs(self) -> BatterySpecs:
        """Load battery specifications from file or use defaults"""
        try:
            with open("battery_specs.json", "r") as f:
                specs_data = json.load(f)
                return BatterySpecs(**specs_data.get("battery_specifications", {}))
        except FileNotFoundError:
            logger.warning("battery_specs.json not found, using defaults")
            return BatterySpecs()
        except Exception as e:
            logger.error(f"Error loading battery specs: {e}")
            return BatterySpecs()
    
    async def add_performance_data(self, data: BatteryPerformance):
        """Add new performance data and update history"""
        self.performance_history.append(data)
        
        # Keep only last 1000 entries to manage memory
        if len(self.performance_history) > 1000:
            self.performance_history.pop(0)
        
        # Store in MongoDB if available
        if self.db:
            try:
                await self.db.battery_performance.insert_one({
                    "timestamp": data.timestamp,
                    "pack_voltage": data.pack_voltage,
                    "pack_current": data.pack_current,
                    "cell_temp": data.cell_temp,
                    "capacity_remaining": data.capacity_remaining,
                    "cycle_count": data.cycle_count,
                    "age_months": data.age_months,
                    "health_score": data.health_score,
                    "source": "battery_ai_predictor"
                })
            except Exception as e:
                logger.error(f"Failed to store performance data: {e}")
        
        logger.info(f"Added performance data: V={data.pack_voltage}V, "
                   f"I={data.pack_current}A, Health={data.health_score}%")
    
    async def predict_battery_life(self) -> BatteryPrediction:
        """Generate battery life prediction using AI or analytical methods"""
        if len(self.performance_history) < 10:
            logger.warning("Insufficient data for prediction. Need at least 10 data points.")
            return BatteryPrediction(
                timestamp=datetime.now().timestamp(),
                remaining_life_hours=0,
                remaining_cycles=0,
                degradation_rate=0,
                confidence_score=0
            )
        
        if self.ai_enabled:
            return await self.predict_battery_life_ai()
        else:
            return self.predict_battery_life_analytical()
    
    async def predict_battery_life_ai(self) -> BatteryPrediction:
        """Use Gemini AI for battery life prediction"""
        try:
            # Prepare data for AI analysis
            analysis_data = self.prepare_ai_analysis_data()
            
            # Create prompt for Gemini
            prompt = self.create_ai_prompt(analysis_data)
            
            # Call Gemini API
            ai_response = await self.call_gemini_api(prompt)
            
            # Parse AI response
            prediction = self.parse_ai_response(ai_response)
            
        except Exception as e:
            logger.error(f"AI prediction failed: {e}")
            prediction = self.predict_battery_life_analytical()
        
        # Store prediction
        self.prediction_history.append(prediction)
        
        # Store in MongoDB if available
        if self.db:
            try:
                await self.db.battery_predictions.insert_one({
                    "timestamp": prediction.timestamp,
                    "remaining_life_hours": prediction.remaining_life_hours,
                    "remaining_cycles": prediction.remaining_cycles,
                    "degradation_rate": prediction.degradation_rate,
                    "confidence_score": prediction.confidence_score,
                    "recommendations": prediction.recommendations or [],
                    "source": "battery_ai_predictor"
                })
            except Exception as e:
                logger.error(f"Failed to store prediction: {e}")
        
        return prediction
    
    def predict_battery_life_analytical(self) -> BatteryPrediction:
        """Use analytical methods for battery life prediction"""
        if len(self.performance_history) < 5:
            return BatteryPrediction(
                timestamp=datetime.now().timestamp(),
                remaining_life_hours=0,
                remaining_cycles=0,
                degradation_rate=0,
                confidence_score=0
            )
        
        # Calculate averages
        avg_health = sum(d.health_score for d in self.performance_history) / len(self.performance_history)
        avg_voltage = sum(d.pack_voltage for d in self.performance_history) / len(self.performance_history)
        avg_temp = sum(d.cell_temp for d in self.performance_history) / len(self.performance_history)
        
        # Estimate degradation rate
        degradation_rate = self.calculate_degradation_rate(avg_health, avg_temp)
        
        # Calculate remaining cycles
        current_cycles = self.performance_history[-1].cycle_count
        remaining_cycles = max(0, self.specs.max_cycles - current_cycles)
        
        # Calculate remaining life
        remaining_life_hours = self.calculate_remaining_life_hours()
        
        prediction = BatteryPrediction(
            timestamp=datetime.now().timestamp(),
            remaining_life_hours=remaining_life_hours,
            remaining_cycles=remaining_cycles,
            degradation_rate=degradation_rate,
            confidence_score=0.7,  # Medium confidence for analytical
            recommendations=self.generate_recommendations(avg_health, avg_temp)
        )
        
        self.prediction_history.append(prediction)
        return prediction
    
    def prepare_ai_analysis_data(self) -> str:
        """Prepare battery data for AI analysis"""
        data = []
        data.append("Battery Performance Analysis Data:\n\n")
        
        # Recent performance data
        data.append("Recent Performance (last 10 readings):\n")
        start = max(0, len(self.performance_history) - 10)
        for i in range(start, len(self.performance_history)):
            perf = self.performance_history[i]
            data.append(f"Time: {perf.timestamp}s, "
                       f"Voltage: {perf.pack_voltage}V, "
                       f"Current: {perf.pack_current}A, "
                       f"Temp: {perf.cell_temp}°C, "
                       f"Health: {perf.health_score}%, "
                       f"Cycles: {perf.cycle_count}\n")
        
        # Battery specifications
        data.append(f"\nBattery Specifications:\n")
        data.append(f"Nominal Capacity: {self.specs.nominal_capacity_ah} Ah\n")
        data.append(f"Nominal Voltage: {self.specs.nominal_voltage} V\n")
        data.append(f"Max Cycles: {self.specs.max_cycles}\n")
        data.append(f"Max Temperature: {self.specs.max_temp}°C\n")
        data.append(f"Min Temperature: {self.specs.min_temp}°C\n")
        data.append(f"Max Current: {self.specs.max_current} A\n")
        data.append(f"Chemistry: {self.specs.chemistry}\n")
        
        # Performance statistics
        data.append(f"\nPerformance Statistics:\n")
        data.append(f"Total Data Points: {len(self.performance_history)}\n")
        data.append(f"Average Health: {self.calculate_average_health()}%\n")
        data.append(f"Average Temperature: {self.calculate_average_temperature()}°C\n")
        data.append(f"Temperature Range: {self.calculate_temperature_range()}°C\n")
        
        return "".join(data)
    
    def create_ai_prompt(self, analysis_data: str) -> str:
        """Create prompt for Gemini AI"""
        prompt = f"""You are an expert battery systems engineer. Analyze the following battery performance data and provide predictions for battery life and health.

{analysis_data}

Please provide a detailed analysis including:
1. Predicted remaining battery life in hours
2. Estimated remaining charge cycles
3. Current degradation rate
4. Confidence score (0-1)
5. Specific recommendations for battery maintenance

Format your response as JSON with the following structure:
{{
  "remaining_life_hours": <float>,
  "remaining_cycles": <float>,
  "degradation_rate": <float>,
  "confidence_score": <float>,
  "recommendations": ["<string>", "<string>"]
}}

Consider factors like temperature effects, cycle count, voltage patterns, and aging when making your predictions."""
        
        return prompt
    
    async def call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API with the given prompt"""
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not provided")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.gemini_api_key}"
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            response = requests.post(
                self.gemini_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
    
    def parse_ai_response(self, response: str) -> BatteryPrediction:
        """Parse AI response and extract prediction data"""
        try:
            response_data = json.loads(response)
            content = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Try to extract JSON from the response
            json_start = content.find('{')
            json_end = content.rfind('}')
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end + 1]
                prediction_data = json.loads(json_str)
                
                return BatteryPrediction(
                    timestamp=datetime.now().timestamp(),
                    remaining_life_hours=prediction_data.get("remaining_life_hours", 0.0),
                    remaining_cycles=prediction_data.get("remaining_cycles", 0.0),
                    degradation_rate=prediction_data.get("degradation_rate", 0.0),
                    confidence_score=prediction_data.get("confidence_score", 0.5),
                    recommendations=prediction_data.get("recommendations", [])
                )
            else:
                logger.warning("Could not parse JSON from AI response")
                return self.predict_battery_life_analytical()
                
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self.predict_battery_life_analytical()
    
    def calculate_degradation_rate(self, avg_health: float, avg_temp: float) -> float:
        """Calculate battery degradation rate"""
        # Base degradation rate
        base_rate = (100.0 - avg_health) / 100.0 * 0.1
        
        # Temperature factor
        temp_factor = 1.0
        if avg_temp > 45.0:
            temp_factor = 1.5 + (avg_temp - 45.0) * 0.1
        elif avg_temp < 10.0:
            temp_factor = 1.2
        
        return base_rate * temp_factor
    
    def calculate_remaining_life_hours(self) -> float:
        """Calculate remaining battery life in hours"""
        if len(self.performance_history) < 2:
            return 0.0
        
        # Calculate average current draw
        avg_current = sum(abs(d.pack_current) for d in self.performance_history) / len(self.performance_history)
        
        if avg_current <= 0:
            return 0.0
        
        # Estimate remaining capacity
        remaining_capacity = self.performance_history[-1].capacity_remaining / 100.0 * self.specs.nominal_capacity_ah
        
        return remaining_capacity / avg_current
    
    def calculate_average_health(self) -> float:
        """Calculate average battery health"""
        if not self.performance_history:
            return 0.0
        return sum(d.health_score for d in self.performance_history) / len(self.performance_history)
    
    def calculate_average_temperature(self) -> float:
        """Calculate average temperature"""
        if not self.performance_history:
            return 0.0
        return sum(d.cell_temp for d in self.performance_history) / len(self.performance_history)
    
    def calculate_temperature_range(self) -> float:
        """Calculate temperature range"""
        if not self.performance_history:
            return 0.0
        
        temps = [d.cell_temp for d in self.performance_history]
        return max(temps) - min(temps)
    
    def generate_recommendations(self, health: float, temp: float) -> List[str]:
        """Generate maintenance recommendations"""
        recommendations = []
        
        if health < 80:
            recommendations.append("Consider battery replacement soon")
        elif health < 90:
            recommendations.append("Monitor battery health closely")
        
        if temp > 45:
            recommendations.append("High temperature detected - check cooling system")
        elif temp < 10:
            recommendations.append("Low temperature - consider warming system")
        
        if len(self.performance_history) > 100:
            recommendations.append("Schedule preventive maintenance")
        
        return recommendations
    
    def enable_ai(self, api_key: str):
        """Enable AI predictions with API key"""
        self.gemini_api_key = api_key
        self.ai_enabled = True
        logger.info("AI prediction enabled")
    
    def disable_ai(self):
        """Disable AI predictions"""
        self.ai_enabled = False
        logger.info("AI prediction disabled")
    
    def get_prediction_report(self) -> Dict:
        """Get latest prediction report"""
        if not self.prediction_history:
            return {"error": "No predictions available"}
        
        latest = self.prediction_history[-1]
        return {
            "timestamp": latest.timestamp,
            "remaining_life_hours": round(latest.remaining_life_hours, 1),
            "remaining_cycles": round(latest.remaining_cycles, 0),
            "degradation_rate": round(latest.degradation_rate, 3),
            "confidence_score": round(latest.confidence_score, 2),
            "recommendations": latest.recommendations or [],
            "ai_enabled": self.ai_enabled
        }

# Example usage
if __name__ == "__main__":
    async def test_predictor():
        # Initialize predictor
        predictor = BatteryAIPredictor()
        
        # Add sample data
        for i in range(20):
            data = BatteryPerformance(
                timestamp=datetime.now().timestamp() + i * 3600,
                pack_voltage=350.0 + (i % 10) * 2.0,
                pack_current=50.0 + (i % 5) * 10.0,
                cell_temp=25.0 + (i % 3) * 5.0,
                capacity_remaining=85.0 - i * 0.5,
                cycle_count=i * 10,
                age_months=6.0 + i * 0.5,
                health_score=90.0 - i * 0.8
            )
            await predictor.add_performance_data(data)
        
        # Make prediction
        prediction = await predictor.predict_battery_life()
        
        # Print results
        report = predictor.get_prediction_report()
        print("=== AI Battery Life Prediction Report ===")
        print(json.dumps(report, indent=2))
        print("==========================================")
    
    # Run test
    asyncio.run(test_predictor()) 