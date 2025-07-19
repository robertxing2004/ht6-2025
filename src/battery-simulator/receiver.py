import socket
import struct

HOST = "0.0.0.0"  # Listen on all interfaces, or use "127.0.0.1" for local only
PORT = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Listening on {HOST}:{PORT}...")
    conn, addr = s.accept()
    print(f"Connected by {addr}")
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(16)  # 4 floats x 4 bytes each = 16 bytes
            if not data:
                break
            # Unpack the 4 floats
            time_s, pack_voltage_v, pack_current_a, cell_temp_c = struct.unpack('<ffff', data)
            print(f"Time: {time_s:.1f}s, Voltage: {pack_voltage_v:.2f}V, Current: {pack_current_a:.2f}A, Temp: {cell_temp_c:.2f}C")
