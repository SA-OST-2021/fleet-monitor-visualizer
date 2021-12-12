# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 10:52:56 2021

@author: florian.baumgartner
"""

import numpy as np
import pandas as pd
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

pio.renderers.default = "browser"
pd.options.mode.chained_assignment = None

fileName = "Dump_211117.txt"

pgnNameTable = {
    'FEE9': "Fuel Consumption: LFC",
    'FEFC': "Dash Display 1: DD1",
    'F004': "Electronic Engine Controller #1: EEC1",
    'FEE5': "Engine Hours, Revolutions: HOURS",
    'FEEC': "Vehicle Identification: VI",
    'FDD1': "MS-standard Interface Identity / Capabilities: FMS",
    'FEC1': "High Resolution Vehicle Distance: VDHR",
    'FE6C': "Tachograph : TCO1",
    'FEEE': "Engine Temperature 1: ET1",
    'FEF5': "Ambient Conditions: AMB",
    'FE6B': "Driver's Identification: DI",
    'FEF2': "Fuel Economy: LFE",
    'FEAE': "Air Supply Pressure : AIR1",
    'FD09': "High Resolution Fuel Consumption (Liquid): HRLFC",
    'FE56': "Aftertreatment 1 Diesel Exhaust Fluid Tank 1 Information: AT1T1I",
    'FD7D': "FMS Tell Tale Status: FMS1",
    'F001': "Electronic Brake Controller 1: EBC1",
    'FDC2': "Electronic Engine Controller 14: EEC14",
    'FEAF': "Fuel Consumption (Gaseous): GFC",
    'F000': "Electronic Retarder Controller 1: ERC1",
    'FEF1': "Cruise Control/Vehicle Speed 1: CCVS1",
    'F003': "Electronic Engine Controller #2: EEC2",
    'FEEA': "Vehicle Weight: VW",
    'FEC0': "Service Information: SERV",
    'FDA4': "PTO Drive Engagement: PTODE",
    'FE70': "Combination Vehicle Weight: CVW",
    'FE4E': "Door Control 1: DC1",
    'FDA5': "Door Control 2: DC2",
    'FEE6': "Time / Date : TD",
    'FED5': "Alternator Speed : AS",
    'F005': "Electronic Transmission Controller 2 : ETC2",
    'FE58': "Air Suspension Control 4 : ASC4",
    'FCB7': "Vehicle Electrical Power #4 : VEP4",
    'F009': "Vehicle Dynamic Stability Control 2 : VDC2",
}


data = []
with open(fileName) as file:
    for l in file.readlines():
        l = l.split()
        s = {"time":     float(l[0].strip("()")),
             "priority": int(l[2][:2], 16),
             "pgn":      int(l[2][2:6], 16),
             "source":   int(l[2][6:], 16),
             "data":     bytearray([int(d, 16) for d in l[4:]])}
        for n in range(8):
            s[f"{n}"] = int(l[4 + n], 16)
        data.append(s)

df = pd.DataFrame(data, columns=["time", "priority", "pgn", "source", "data",
                                 "0", "1", "2", "3", "4", "5", "6", "7"])
df["date"] = pd.to_datetime(df["time"], unit="s")
pgnTypes = list(np.unique(df[["pgn"]].values))
for pgn in pgnTypes:
    if(f"{pgn:04X}" in pgnNameTable):
        print(f"{pgn:04X}: " + pgnNameTable[f"{pgn:04X}"])
    else:
        print(f"{pgn:04X}")


df = df[df["date"] > '2021-11-17 16:00:00']  # Only for generating visualization!



tachograph = df[df["pgn"] == 0xFE6C]
tachograph["speed"] = tachograph["7"] + tachograph["6"] / 256.0

fuelConsumption = df[df["pgn"] == 0xFD09]
fuelConsumption["fuelConsumption"] = (fuelConsumption["4"] + 
                                      fuelConsumption["5"] * 256 + 
                                      fuelConsumption["6"] * 256**2  +
                                      fuelConsumption["7"] * 256**3) / 1000.0
fuelConsumption["fuelConsumption"] -= fuelConsumption["fuelConsumption"].iloc[0]

fuelEconomy = df[df["pgn"] == 0xFEF2]
fuelEconomy["fuelRate"] = (fuelEconomy["0"] + 
                           fuelEconomy["1"] * 256) * 0.05
fuelEconomy["fuelEconomy"] = (fuelEconomy["2"] + 
                              fuelEconomy["3"] * 256) / 512


doors = df[df["pgn"] == 0xFDA5]
doorStatus = {0x00: "closed", 0x01: "open", 0x02: "error", 0x03: "not available"}
doors["door1"] = pd.Series((doors["0"] & 0x0C) // 4).map(doorStatus)
doors["door2"] = pd.Series(doors["1"] & 0x03).map(doorStatus)

suspension = df[df["pgn"] == 0xFE58]
suspension["suspension"] = (suspension["0"] + 
                            suspension["1"] * 256 + 
                            suspension["2"] * 256**2  +
                            suspension["3"] * 256**3  +
                            suspension["4"] * 256**4  +
                            suspension["5"] * 256**5  +
                            suspension["6"] * 256**6  +
                            suspension["7"] * 256**7) / 10.0

temperature = df[df["pgn"] == 0xFEEE]
temperature["temperature"] = temperature["0"] - 40.0

diselExhaustFluid = df[df["pgn"] == 0xFE56]
diselExhaustFluid["diselExhaustFluid"] = diselExhaustFluid["0"] * 0.4

ambientAir = df[df["pgn"] == 0xFEF5]
ambientAir["ambientAir"] = (ambientAir["3"] + ambientAir["4"] * 256) * 0.03125 - 273.0

alternator = df[df["pgn"] == 0xFED5]
alternator["alternatorSpeed"] = (alternator["0"] + alternator["1"] * 256) / 8.0
alternatorStatus = {0x00: "not charging", 0x01: "charging", 0x02: "error", 0x03: "not available"}
alternator["alternator1"] = pd.Series((alternator["2"] & 0x03) // 1).map(alternatorStatus)
alternator["alternator2"] = pd.Series((alternator["2"] & 0x0C) // 4).map(alternatorStatus)
alternator["alternator3"] = pd.Series((alternator["2"] & 0x30) // 16).map(alternatorStatus)
alternator["alternator4"] = pd.Series((alternator["2"] & 0xC0) // 64).map(alternatorStatus)

vehicleDistance = df[df["pgn"] == 0xFEC1]
vehicleDistance["vehicleDistance"] = (vehicleDistance["0"] + 
                                      vehicleDistance["1"] * 256 + 
                                      vehicleDistance["2"] * 256**2  +
                                      vehicleDistance["3"] * 256**3) * 5.0
vehicleDistance["vehicleDistance"] -= vehicleDistance["vehicleDistance"].iloc[0]

airPressure = df[df["pgn"] == 0xFEAE]
airPressure["airPressure"] = (airPressure["2"] + airPressure["3"] * 256) * 8.0
# airPressure["airPressure"] -= min(airPressure["airPressure"])

cruiseControl = df[df["pgn"] == 0xFEF1]
# cruiseControl["parkBreak"] = pd.Series((cruiseControl["0"] & 0x04) // 4)
cruiseControl["wheelSpeed"] = cruiseControl["1"] + cruiseControl["2"] / 256.0
cruiseControl["clutchSwitch"] = pd.Series((cruiseControl["3"] & 0x40) // 64)
cruiseControl["breakSwitch"] = pd.Series((cruiseControl["3"] & 0x10) // 16)
cruiseControl["cruiseControl"] = pd.Series(cruiseControl["3"] & 0x01)
cruiseControlStatus = {0x00: "off", 0x01: "hold", 0x02: "accelerate", 0x03: "decelerate", 0x04: "resume", 0x05: "set", 0x06: "accel. override", 0x07: "not available"}
cruiseControl["cruiseControlState"] = pd.Series((cruiseControl["6"] & 0xE0) // 32).map(cruiseControlStatus)
cruiseControlPtoStatus = {0x00: "off", 0x05: "set", 0x1F: "not available"}
cruiseControl["cruiseControlPto"] = pd.Series(cruiseControl["6"] & 0x1F).map(cruiseControlPtoStatus)


engineController1 = df[df["pgn"] == 0xF004]
engineController1["engineTorque"] = engineController1["2"] - 125.0
engineController1["engineSpeed"] = (engineController1["3"] + engineController1["4"] * 256) / 8.0

engineController2 = df[df["pgn"] == 0xF003]
engineController2["acceleratorPedal"] = engineController2["1"] * 0.4
engineController2["engineLoad"] = engineController2["2"] * 0.4


fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                    vertical_spacing = 0.065,
                    subplot_titles=["Vehicle Speed [km/h]",
                                    "Accelerator Pedal [%]",
                                    "Fuel Consumption [l]",
                                    "  Door Open State        "])

fig.add_trace(go.Scatter(x=tachograph["date"], y=tachograph["speed"],
                         name="Vehicle Speed [km/h]",
                         fill="tozeroy"), row=1, col=1)

fig.add_trace(go.Scatter(x=engineController2["date"], y=engineController2["acceleratorPedal"],
                          name="Accelerator Pedal [%]",
                          fill="tozeroy"), row=2, col=1)

fig.add_trace(go.Scatter(x=fuelConsumption["date"], y=fuelConsumption["fuelConsumption"],
                         name="Fuel Consumption [l]",
                         fill="tozeroy"), row=3, col=1)


doorStatus1 = {"closed": "1 closed", "open": "1 open"}
doorStatus2 = {"closed": "2 closed", "open": "2 open"}
doors["door1"] = pd.Series(doors["door1"]).map(doorStatus1)
doors["door2"] = pd.Series(doors["door2"]).map(doorStatus2)

fig.add_trace(go.Scatter(x=doors["date"], y=doors["door2"],
                          name="Door 2 Open State"), row=4, col=1)

fig.add_trace(go.Scatter(x=doors["date"], y=doors["door1"],
                          name="Door 1 Open State"), row=4, col=1)


# fig.add_trace(go.Scatter(x=alternator["date"], y=alternator["alternatorSpeed"],
#                           name="Alternator Speed [rpm]",
#                           fill="tozeroy"), row=2, col=1)

# fig.add_trace(go.Scatter(x=engineController1["date"], y=engineController1["engineSpeed"],
#                           name="Engine Speed [rpm]",
#                           fill="tozeroy"), row=2, col=1)


# fig.add_trace(go.Scatter(x=fuelEconomy["date"], y=fuelEconomy["fuelRate"],
#                          name="Fuel Rate [l/h]",
#                          fill="tozeroy"), row=4, col=1)

# fig.add_trace(go.Scatter(x=fuelEconomy["date"], y=fuelEconomy["fuelEconomy"],
#                          name="Fuel Economy [km/l]",
#                          fill="tozeroy"), row=5, col=1)

# fig.add_trace(go.Scatter(x=engineController2["date"], y=engineController2["engineLoad"],
#                           name="Engine Load [%]",
#                           fill="tozeroy"), row=5, col=1)

# fig.add_trace(go.Scatter(x=engineController1["date"], y=engineController1["engineTorque"],
#                           name="Engine Torque [%]",
#                           fill="tozeroy"), row=5, col=1)

# fig.add_trace(go.Scatter(x=cruiseControl["date"], y=cruiseControl["breakSwitch"],
#                           name="Break Pedal",
#                           fill="tozeroy"), row=7, col=1)

# fig.add_trace(go.Scatter(x=cruiseControl["date"], y=cruiseControl["clutchSwitch"],
#                           name="Clutch Switch",
#                           fill="tozeroy"), row=8, col=1)

# fig.add_trace(go.Scatter(x=airPressure["date"], y=airPressure["airPressure"],
#                           name="Air Supply Pressure [kPa]",
#                           fill="tozeroy"), row=7, col=1)

# fig.add_trace(go.Scatter(x=vehicleDistance["date"], y=vehicleDistance["vehicleDistance"],
#                           name="Vehicle Distance [m]",
#                           fill="tozeroy"), row=7, col=1)

# fig.add_trace(go.Scatter(x=suspension["date"], y=suspension["suspension"],
#                           name="Air Suspension Control [kPa]",
#                           fill="tozeroy"), row=5, col=1)

# fig.add_trace(go.Scatter(x=temperature["date"], y=temperature["temperature"],
#                           name="Engine Temperature [°C]",
#                           fill="tozeroy"), row=6, col=1)

# fig.add_trace(go.Scatter(x=ambientAir["date"], y=ambientAir["ambientAir"],
#                           name="Ambient Air [°C]",
#                           fill="tozeroy"), row=7, col=1)

# fig.add_trace(go.Scatter(x=diselExhaustFluid["date"], y=diselExhaustFluid["diselExhaustFluid"],
#                           name="Diesel Exhaust Fluid Tank 1 Information [%]",
#                           fill="tozeroy"), row=8, col=1)



fig.update_annotations(font=dict(size=18))
for i in fig.layout.annotations:
    i.update(x=0.06, yshift=6)

gray = "#CCCCCC"
fig.update_layout(showlegend=False)
fig.update_yaxes(ticks="outside", tickwidth=2, tickcolor='white', ticklen=5,
                 linewidth=1.1, linecolor=gray, gridwidth=1.1, gridcolor=gray,
                 tickfont=dict(size=15))
fig.update_xaxes(ticks="outside", tickwidth=2, tickcolor='white', ticklen=10,
                 linewidth=1.1, linecolor=gray, gridwidth=1.1, gridcolor=gray,
                 tickfont=dict(size=15))

fig['layout']['yaxis3'].tickvals = [0, 0.25, 0.5, 0.75, 1.0, 1.25]

fig.update_layout(width=2000, height=1100, template="plotly_white")#, title_text=fileName)
fig.show()
fig.write_html("plot.html")
fig.write_image("plot.svg")
fig.write_image("plot.pdf")
