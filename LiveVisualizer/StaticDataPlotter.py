# -*- coding: utf-8 -*-
"""
Created on Thu Dec 30 00:19:00 2021

@author: Admin
"""

import os
import time
import pathlib
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

pio.renderers.default = "browser"
pd.options.mode.chained_assignment = None


filepath = pathlib.Path(r"C:\Users\Admin\GoogleDrive\HSR\SA-OST-2021\fleet-monitor-network-tool\data")
files = os.listdir(filepath)

df = pd.DataFrame()
for file in files:
    tmp = pd.read_csv(filepath / file, header=None)  
    tmp = tmp.iloc[: , 1:]                     # Remove index column
    tmp[1] = pd.to_datetime(tmp[1], unit="s")  # Convert Unix Timestamp
    tmp = tmp.rename({1: "date", 2: "pgn", 3: "data", 4: "name"}, axis=1)
    tmp = tmp[tmp["date"] > '2020-01-01 00:00:00']
    tmp["pgn"] = tmp["pgn"].apply(int, base=16)
    for i in range(8):
        tmp[f"{7-i}"] = pd.Series((tmp["data"].apply(int, base=16) // 2**(8*i)) & 0xFF)
    df = df.append(tmp)


print(len(set(df["name"].values.tolist())))


tachograph = df[df["pgn"] == 0xFE6C]
tachograph["speed"] = tachograph["7"] + tachograph["6"] / 256.0

engineController1 = df[df["pgn"] == 0xF004]
engineController1["engineTorque"] = engineController1["2"] - 125.0
engineController1["engineSpeed"] = (engineController1["3"] + engineController1["4"] * 256) / 8.0

engineController2 = df[df["pgn"] == 0xF003]
engineController2["acceleratorPedal"] = engineController2["1"] * 0.4
engineController2["engineLoad"] = engineController2["2"] * 0.4

ambientAir = df[df["pgn"] == 0xFEF5]
ambientAir["ambientAir"] = (ambientAir["3"] + ambientAir["4"] * 256) * 0.03125 - 273.0

temperature = df[df["pgn"] == 0xFEEE]
temperature["temperature"] = temperature["0"] - 40.0

fuelConsumption = df[df["pgn"] == 0xFEE9]
fuelConsumption["fuelConsumption"] = (fuelConsumption["4"] + 
                                      fuelConsumption["5"] * 256 + 
                                      fuelConsumption["6"] * 256**2  +
                                      fuelConsumption["7"] * 256**3) * 0.5
fuelConsumption["fuelConsumption"] -= fuelConsumption["fuelConsumption"].iloc[0]




fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                    vertical_spacing = 0.065,
                    subplot_titles=["Vehicle Speed [km/h]",
                                    "Accelerator Pedal [%]",
                                    "Fuel Consumption [l]",
                                    "  Door Open State        "])

# fig.add_trace(go.Scatter(x=tachograph["date"], y=tachograph["speed"],
#                           name="Vehicle Speed [km/h]",
#                           fill="tozeroy"), row=1, col=1)

# fig.add_trace(go.Scatter(x=temperature["date"], y=temperature["temperature"],
#                           name="Engine Temperature [°C]",
#                           fill="tozeroy"), row=1, col=1)

# fig.add_trace(go.Scatter(x=ambientAir["date"], y=ambientAir["ambientAir"],
#                           name="Ambient Air [°C]",
#                           fill="tozeroy"), row=2, col=1)


# fig.update_layout(width=2000, height=1100, template="plotly_white")#, title_text=fileName)

# fig.show()

