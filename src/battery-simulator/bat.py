import pybamm
import numpy as np
import pandas as pd

# pack configuration
num_series = 96
num_parallel = 72

# load a standard lithium-ion cell model
model = pybamm.lithium_ion.DFN()

# load default parameters
param = model.default_parameter_values

# get single cell capacity (A.h) from parameters
single_cell_capacity = param["Nominal cell capacity [A.h]"]

# calculate nominal pack voltage (approximate)
nominal_cell_voltage = 3.7  # typical Li-ion cell nominal voltage (V)
nominal_pack_voltage = nominal_cell_voltage * num_series

# example: discharge power = 5 kW (typical for home storage use)
power_discharge = 5000  # watts

# calculate approx current per pack: I = P / V
current_pack = power_discharge / nominal_pack_voltage

# update parameters to emulate pack behavior
param.update({
    # scale capacity by parallel strings
    "Nominal cell capacity [A.h]": single_cell_capacity * num_parallel,
    
    "Lower voltage cut-off [V]": 2.5,
    "Upper voltage cut-off [V]": 4.1,
    
    # internal resistance rise and degradation tweaks (example for used battery)
    "Contact resistance [Ohm]": 0.0025,
    "Negative electrode conductivity [S.m-1]": 1000,
    "Positive electrode conductivity [S.m-1]": 1500,
    "Negative electrode active material volume fraction": 0.7,
    "Positive electrode active material volume fraction": 0.75,
    "Negative particle diffusivity [m2.s-1]": 1e-14,
    "Positive particle diffusivity [m2.s-1]": 5e-14,
    "Negative electrode exchange-current density [A.m-2]": 1.0,
    "Positive electrode exchange-current density [A.m-2]": 1.5,

    "Current function [A]": current_pack
})

# create simulation
sim = pybamm.Simulation(model, parameter_values=param)

# create time evaluation array (simulate 1 hour discharge)
t_eval = pybamm.linspace(0, 3600, 100)
t_eval_np = t_eval.entries.squeeze()

# solve simulation
sol = sim.solve(t_eval=t_eval_np)

# extract key results
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

print(df.head())