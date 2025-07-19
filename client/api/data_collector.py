#!/usr/bin/env python3
"""
Data Collector for QNX Battery Monitoring System
Receives data from battery_monitor.cpp and battery_ai_predictor.cpp
and forwards it to the FastAPI backend for storage in MongoDB Atlas.
"""

import socket
import struct
import json
import time
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BatteryDataCollector:
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.battery_monitor_port = 23456
        self.ai_predictor_port = 23457  # Assuming AI predictor uses different port
        self.running = False
        self.data_queue = queue.Queue()
        
        # Data structures to match C++ structs
        self.battery_data_buffer = []
        self.performance_data_buffer = []
        self.prediction_data_buffer = []
        
    def start(self):
        """Start the data collector"""
        self.running = True
        logger.info("Starting Battery Data Collector...")
        
        # Start data collection threads
        battery_thread = threading.Thread(target=self.collect_battery_data, daemon=True)
        ai_thread = threading.Thread(target=self.collect_ai_data, daemon=True)
        api_thread = threading.Thread(target=self.send_to_api, daemon=True)
        
        battery_thread.start()
        ai_thread.start()
        api_thread.start()
        
        logger.info("Data collector started successfully")
        
    def stop(self):
        """Stop the data collector"""
        self.running = False
        logger.info("Stopping Battery Data Collector...")
        
    def collect_battery_data(self):
        """Collect data from battery_monitor.cpp"""
        logger.info(f"Starting battery data collection on port {self.battery_monitor_port}")
        
        try:
            # Create socket to receive data from battery_monitor.cpp
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('localhost', self.battery_monitor_port))
                server_socket.listen(1)
                server_socket.settimeout(1.0)  # 1 second timeout
                
                while self.running:
                    try:
                        client_socket, address = server_socket.accept()
                        logger.info(f"Battery monitor connected from {address}")
                        
                        with client_socket:
                            while self.running:
                                # Receive 4 floats (timestamp, pack_voltage, pack_current, cell_temp)
                                data = client_socket.recv(16)  # 4 floats * 4 bytes
                                if not data:
                                    break
                                    
                                if len(data) == 16:
                                    timestamp, pack_voltage, pack_current, cell_temp = struct.unpack('<ffff', data)
                                    
                                    battery_data = {
                                        "timestamp": timestamp,
                                        "pack_voltage": pack_voltage,
                                        "pack_current": pack_current,
                                        "cell_temp": cell_temp,
                                        "source": "battery_monitor"
                                    }
                                    
                                    logger.info(f"Received battery data: {battery_data}")
                                    self.data_queue.put(("battery_data", battery_data))
                                    
                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.error(f"Error in battery data collection: {e}")
                        time.sleep(1)
                        
        except Exception as e:
            logger.error(f"Failed to start battery data collection: {e}")
            
    def collect_ai_data(self):
        """Collect data from battery_ai_predictor.cpp"""
        logger.info(f"Starting AI data collection on port {self.ai_predictor_port}")
        
        try:
            # Create socket to receive data from battery_ai_predictor.cpp
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('localhost', self.ai_predictor_port))
                server_socket.listen(1)
                server_socket.settimeout(1.0)  # 1 second timeout
                
                while self.running:
                    try:
                        client_socket, address = server_socket.accept()
                        logger.info(f"AI predictor connected from {address}")
                        
                        with client_socket:
                            while self.running:
                                # Receive JSON data from AI predictor
                                data = client_socket.recv(4096)
                                if not data:
                                    break
                                    
                                try:
                                    json_data = json.loads(data.decode('utf-8'))
                                    
                                    # Handle different types of AI data
                                    if "capacity_remaining" in json_data:
                                        # Performance data
                                        performance_data = {
                                            "timestamp": json_data.get("timestamp", time.time()),
                                            "pack_voltage": json_data.get("pack_voltage", 0),
                                            "pack_current": json_data.get("pack_current", 0),
                                            "cell_temp": json_data.get("cell_temp", 0),
                                            "capacity_remaining": json_data.get("capacity_remaining", 0),
                                            "cycle_count": json_data.get("cycle_count", 0),
                                            "age_months": json_data.get("age_months", 0),
                                            "health_score": json_data.get("health_score", 0),
                                            "source": "battery_ai_predictor"
                                        }
                                        self.data_queue.put(("performance", performance_data))
                                        
                                    elif "remaining_life_hours" in json_data:
                                        # Prediction data
                                        prediction_data = {
                                            "timestamp": json_data.get("timestamp", time.time()),
                                            "remaining_life_hours": json_data.get("remaining_life_hours", 0),
                                            "remaining_cycles": json_data.get("remaining_cycles", 0),
                                            "degradation_rate": json_data.get("degradation_rate", 0),
                                            "source": "battery_ai_predictor"
                                        }
                                        self.data_queue.put(("prediction", prediction_data))
                                        
                                    logger.info(f"Received AI data: {json_data}")
                                    
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse JSON data: {e}")
                                    
                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.error(f"Error in AI data collection: {e}")
                        time.sleep(1)
                        
        except Exception as e:
            logger.error(f"Failed to start AI data collection: {e}")
            
    def send_to_api(self):
        """Send collected data to FastAPI backend"""
        logger.info("Starting API data sender")
        
        while self.running:
            try:
                # Get data from queue with timeout
                data_type, data = self.data_queue.get(timeout=1.0)
                
                # Send to appropriate API endpoint
                if data_type == "battery_data":
                    self.send_battery_data(data)
                elif data_type == "performance":
                    self.send_performance_data(data)
                elif data_type == "prediction":
                    self.send_prediction_data(data)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error sending data to API: {e}")
                time.sleep(1)
                
    def send_battery_data(self, data: Dict[str, Any]):
        """Send battery data to API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/battery-data",
                json=data,
                timeout=5
            )
            response.raise_for_status()
            logger.debug(f"Battery data sent successfully: {response.json()}")
        except Exception as e:
            logger.error(f"Failed to send battery data: {e}")
            
    def send_performance_data(self, data: Dict[str, Any]):
        """Send performance data to API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/battery-performance",
                json=data,
                timeout=5
            )
            response.raise_for_status()
            logger.debug(f"Performance data sent successfully: {response.json()}")
        except Exception as e:
            logger.error(f"Failed to send performance data: {e}")
            
    def send_prediction_data(self, data: Dict[str, Any]):
        """Send prediction data to API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/battery-prediction",
                json=data,
                timeout=5
            )
            response.raise_for_status()
            logger.debug(f"Prediction data sent successfully: {response.json()}")
        except Exception as e:
            logger.error(f"Failed to send prediction data: {e}")

def main():
    """Main function to run the data collector"""
    collector = BatteryDataCollector()
    
    try:
        collector.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        collector.stop()
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        collector.stop()

if __name__ == "__main__":
    main() 