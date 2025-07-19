import pybamm
import numpy as np
import pandas as pd
import socket
import time
import struct

# CONFIGURATION VALUES

# pack configuration
num_series = 96
num_parallel = 72

# load configuration
power_discharge = 5000  # watts

# create simulation evaluation array (simulate 1 hour discharge)
t_eval = pybamm.linspace(0, 3600, 361)
t_eval_np = t_eval.entries.squeeze()



model = pybamm.lithium_ion.DFN()

param = model.default_parameter_values

single_cell_capacity = param["Nominal cell capacity [A.h]"]

nominal_cell_voltage = 3.7
nominal_pack_voltage = nominal_cell_voltage * num_series

current_pack = power_discharge / nominal_pack_voltage
current_cell = current_pack / num_parallel


param.update({
    "Nominal cell capacity [A.h]": single_cell_capacity * num_parallel,
    "Current function [A]": current_cell,
    
    "Lower voltage cut-off [V]": 2.5,
    "Upper voltage cut-off [V]": 4.1,
    
    # internal resistance rise and degradation tweaks
    "Contact resistance [Ohm]": 0.0025,
    "Negative electrode conductivity [S.m-1]": 1000,
    "Positive electrode conductivity [S.m-1]": 1500,
    "Negative electrode active material volume fraction": 0.7,
    "Positive electrode active material volume fraction": 0.75,
    "Negative particle diffusivity [m2.s-1]": 1e-14,
    "Positive particle diffusivity [m2.s-1]": 5e-14,
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
terminal_voltage_pack = terminal_voltage_cell * num_series

current_cell = sol["Current [A]"].entries
current_pack = current_cell * num_parallel

data = {}
for var in variables_to_export:
    entries = sol[var].entries
    if entries.ndim > 1:
        entries = entries[0, :]
    key = var.lower().replace(" ", "_").replace("[", "").replace("]", "").replace(".", "").replace("-", "_")
    data[key] = entries

df = pd.DataFrame(data)

# Add pack-level columns
df["pack_voltage_v"] = terminal_voltage_pack
df["pack_current_a"] = current_pack

print(df.head())

HOST = "127.0.0.1"
PORT = 23456

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Sender connected to server")
    for i in range(len(df)):
        # pack 4 floats into binary
        message = struct.pack(
            '<ffff',
            float(df["time_s"].iloc[i]),
            float(df["pack_voltage_v"].iloc[i]),
            float(df["pack_current_a"].iloc[i]),
            float(df["cell_temperature_c"].iloc[i])
        )
        s.sendall(message)
        time.sleep(0.1)