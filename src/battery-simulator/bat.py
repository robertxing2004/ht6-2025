import pybamm
import numpy as np
import pandas as pd
import socket
import time
import struct
from dotenv import load_dotenv
import os

# CONFIGURATION VALUES

# Module configuration - one module with three batteries
module_config = {
    "num_series": 96,
    "num_parallel": 72,
    "power_discharge": 5000,  # watts
}

# Individual battery characteristics within the module
battery_characteristics = [
    {
        "name": "Battery_1",
        "capacity_factor": 0.7,  # normal capacity
        "degradation_factor": 1.0,  # normal degradation
        "temperature_offset": 0,  # normal temperature
        "weight": 0.33,  # contributes 33% to module performance
    },
    {
        "name": "Battery_2", 
        "capacity_factor": 0.75,  # 5% lower capacity
        "degradation_factor": 1.2,  # 20% more degradation
        "temperature_offset": 5,  # 5°C higher temperature
        "weight": 0.33,  # contributes 33% to module performance
    },
    {
        "name": "Battery_3",
        "capacity_factor": 0.72,  # 10% lower capacity
        "degradation_factor": 1.4,  # 40% more degradation
        "temperature_offset": 8,  # 8°C higher temperature
        "weight": 0.34,  # contributes 34% to module performance
    }
]

# create simulation evaluation array (simulate 1 hour discharge)
t_eval = pybamm.linspace(0, 3600, 361)
t_eval_np = t_eval.entries.squeeze()

# Store individual battery simulation results
individual_batteries = {}

print("Simulating individual batteries within the module...")

for battery_idx, battery_config in enumerate(battery_characteristics):
    print(f"Simulating {battery_config['name']}...")
    
    model = pybamm.lithium_ion.DFN()
    param = model.default_parameter_values
    
    single_cell_capacity = param["Nominal cell capacity [A.h]"]
    
    nominal_cell_voltage = 3.7
    nominal_pack_voltage = nominal_cell_voltage * module_config["num_series"]
    
    current_pack = module_config["power_discharge"] / nominal_pack_voltage
    current_cell = current_pack / module_config["num_parallel"]
    
    # Apply battery-specific characteristics
    param.update({
        "Nominal cell capacity [A.h]": single_cell_capacity * module_config["num_parallel"] * battery_config["capacity_factor"],
        "Current function [A]": current_cell,
        
        "Lower voltage cut-off [V]": 2.5,
        "Upper voltage cut-off [V]": 4.1,
        
        # Apply degradation factor to internal resistance
        "Contact resistance [Ohm]": 0.0025 * battery_config["degradation_factor"],
        "Negative electrode conductivity [S.m-1]": 1000 / battery_config["degradation_factor"],
        "Positive electrode conductivity [S.m-1]": 1500 / battery_config["degradation_factor"],
        "Negative electrode active material volume fraction": 0.7,
        "Positive electrode active material volume fraction": 0.75,
        "Negative particle diffusivity [m2.s-1]": 1e-14 / battery_config["degradation_factor"],
        "Positive particle diffusivity [m2.s-1]": 5e-14 / battery_config["degradation_factor"],
        "Negative electrode exchange-current density [A.m-2]": 1.0,
        "Positive electrode exchange-current density [A.m-2]": 1.5,
    })
    
    sim = pybamm.Simulation(model, parameter_values=param)
    sol = sim.solve(t_eval=t_eval_np)
    
    variables_to_export = [
        "Time [s]",
        "Terminal voltage [V]",
        "Current [A]",
        "Cell temperature [C]",
    ]
    
    terminal_voltage_cell = sol["Terminal voltage [V]"].entries
    terminal_voltage_pack = terminal_voltage_cell * module_config["num_series"]
    
    current_cell = sol["Current [A]"].entries
    current_pack = current_cell * module_config["num_parallel"]
    
    data = {}
    for var in variables_to_export:
        entries = sol[var].entries
        if entries.ndim > 1:
            entries = entries[0, :]
        key = var.lower().replace(" ", "_").replace("[", "").replace("]", "").replace(".", "").replace("-", "_")
        data[key] = entries
    
    df = pd.DataFrame(data)
    
    # Add pack-level columns with temperature offset
    df["pack_voltage_v"] = terminal_voltage_pack
    df["pack_current_a"] = current_pack
    df["cell_temperature_c"] = df["cell_temperature_c"] + battery_config["temperature_offset"]
    df["battery_name"] = battery_config["name"]
    df["battery_weight"] = battery_config["weight"]
    
    individual_batteries[battery_config["name"]] = df
    print(f"✓ {battery_config['name']} simulation complete")

# Calculate module-level telemetry (weighted average of individual batteries)
print("\nCalculating module-level telemetry...")

module_data = []
# Find the minimum length among all batteries to avoid index errors
min_length = min(len(df) for df in individual_batteries.values())

for i in range(min_length):
    # Weighted average of voltages (only include batteries that have data at this index)
    module_voltage = 0
    module_current = 0
    module_temperature = 0
    total_weight = 0
    
    for df in individual_batteries.values():
        if i < len(df):  # Check if battery has data at this index
            weight = df["battery_weight"].iloc[i]
            module_voltage += df["pack_voltage_v"].iloc[i] * weight
            module_current += df["pack_current_a"].iloc[i] * weight
            module_temperature += df["cell_temperature_c"].iloc[i] * weight
            total_weight += weight
    
    # Normalize by total weight if we have data
    if total_weight > 0:
        module_voltage /= total_weight
        module_current /= total_weight
        module_temperature /= total_weight
    
    # Use timestamp from first battery (they're all the same)
    timestamp = list(individual_batteries.values())[0]["time_s"].iloc[i]
    
    module_data.append({
        "time_s": timestamp,
        "pack_voltage_v": module_voltage,
        "pack_current_a": module_current,
        "cell_temperature_c": module_temperature
    })

module_df = pd.DataFrame(module_data)

print("\nModule Telemetry Preview (first 5 rows):")
print(module_df.head())

print("\nBattery Module Characteristics:")
print(f"  Module Power: {module_config['power_discharge']}W")
print(f"  Configuration: {module_config['num_series']}S x {module_config['num_parallel']}P")
print("\nIndividual Battery Characteristics:")
for battery_config in battery_characteristics:
    print(f"  {battery_config['name']}: {battery_config['capacity_factor']:.1%} capacity, "
          f"{battery_config['degradation_factor']:.1f}x degradation, "
          f"{battery_config['temperature_offset']:+d}°C temp offset, "
          f"{battery_config['weight']:.1%} weight")

load_dotenv()
HOST = os.getenv("HOST")
PORT = 23456

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"\nSender connected to server at {HOST}:{PORT}")
    print("Sending module-level telemetry every 5 seconds...")
    
    # Send module-level data and individual battery data
    for i in range(len(module_df)):
        # Send module telemetry first
        module_message = struct.pack(
            '<ffff',
            float(module_df["time_s"].iloc[i]),
            float(module_df["pack_voltage_v"].iloc[i]),
            float(module_df["pack_current_a"].iloc[i]),
            float(module_df["cell_temperature_c"].iloc[i])
        )
        s.sendall(module_message)
        print(f"Sent Module Telemetry: Time={module_df['time_s'].iloc[i]:.1f}s, "
              f"Voltage={module_df['pack_voltage_v'].iloc[i]:.1f}V, "
              f"Current={module_df['pack_current_a'].iloc[i]:.1f}A, "
              f"Temp={module_df['cell_temperature_c'].iloc[i]:.1f}°C")
        
        # Send individual battery telemetries
        for battery_name, df in individual_batteries.items():
            if i < len(df):  # Only send if battery has data at this index
                battery_message = struct.pack(
                    '<ffff',
                    float(df["time_s"].iloc[i]),
                    float(df["pack_voltage_v"].iloc[i]),
                    float(df["pack_current_a"].iloc[i]),
                    float(df["cell_temperature_c"].iloc[i])
                )
                s.sendall(battery_message)
                print(f"  Sent {battery_name}: Time={df['time_s'].iloc[i]:.1f}s, "
                      f"Voltage={df['pack_voltage_v'].iloc[i]:.1f}V, "
                      f"Current={df['pack_current_a'].iloc[i]:.1f}A, "
                      f"Temp={df['cell_temperature_c'].iloc[i]:.1f}°C")
        
        time.sleep(5.0)  # Send data every 5 seconds