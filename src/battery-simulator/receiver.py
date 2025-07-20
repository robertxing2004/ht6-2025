import socket
import struct
import requests
import time
from datetime import datetime

HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 23456  # Match the port in bat.py
API_ENDPOINT = "http://localhost:8000/api/battery-data"

def send_to_api(data, source="Module"):
    try:
        payload = {
            "timestamp": time.time(),
            "pack_voltage": data[1],  # pack_voltage_v
            "pack_current": data[2],  # pack_current_a
            "cell_temp": data[3],     # cell_temp_c
            "source": source
        }
        response = requests.post(API_ENDPOINT, json=payload)
        if response.status_code == 200:
            print(f"✅ Data sent to API for {source}")
        else:
            print(f"❌ API error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Error sending to API: {e}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Listening on {HOST}:{PORT}...")
    
    while True:
        try:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            with conn:
                while True:
                    data = conn.recv(16)  # 4 floats x 4 bytes each = 16 bytes
                    if not data:
                        break
                    
                    # Unpack the 4 floats
                    values = struct.unpack('<ffff', data)
                    time_s, pack_voltage_v, pack_current_a, cell_temp_c = values
                    
                    # Print received data
                    print(f"Time: {time_s:.1f}s, Voltage: {pack_voltage_v:.2f}V, "
                          f"Current: {pack_current_a:.2f}A, Temp: {cell_temp_c:.2f}C")
                    
                    # Forward to API
                    send_to_api(values)
        except Exception as e:
            print(f"Connection error: {e}")
            time.sleep(1)  # Wait before retrying
