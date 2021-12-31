###############################################################################
# file    dash_test.py
###############################################################################
# brief   Test for dash framework
###############################################################################
# author  Florian Baumgartner
# version 1.0
# date    2021-12-15
###############################################################################
# MIT License
#
# Copyright (c) 2021 Institute for Networked Solutions OST
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################

import os
import sys
import dash
import pathlib
import platform
import pandas as pd
from plotly.subplots import make_subplots
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from datetime import datetime
import webbrowser
import threading

# Inlude file from other directory
importPath = pathlib.Path.cwd().parents[1] / "fleet-monitor-network-tool"
sys.path.insert(0, str(importPath))
from server import HttpServer
sys.path.remove(str(importPath))
systemStartTime = datetime.now()

def runServer():
    if(platform.system() == "Windows"):
        server = HttpServer("10.3.141.176", 50000, False)
    else:
        server = HttpServer("10.3.141.1", 8080, False)
    if(server.start() == False):
        print("Server could not be started")
        sys.exit(1)
    print("Server has started...")



maxDisplayTime = 60  # [s]
df = pd.DataFrame()


app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Graph(id='live-update-graph', animate=True),
    dcc.Interval(id='graph-update', interval=1*1000)
])


@app.callback(
    Output('live-update-graph', 'figure'),
    [ Input('graph-update', 'n_intervals') ]
)
def update_graph_scatter(input_data):
    global df, systemStartTime, maxDisplayTime

    files = sorted(os.listdir(importPath / "data"))
    try:
        index = [int(i.split('.')[0]) for i in files][-1]
    except:
        index = -1
    if(index != update_graph_scatter.fileIndex):
        update_graph_scatter.fileIndex = index
        print(f"We have a new file ready: {files[index]}")
        
        tmp = pd.read_csv(importPath / "data" / files[update_graph_scatter.fileIndex], header=None)  
        tmp = tmp.rename({1: "date", 2: "pgn", 3: "data", 4: "name"}, axis=1)
        tmp["date"] = pd.to_datetime(tmp["date"], unit="s")  # Convert Unix Timestamp
        tmp["pgn"] = tmp["pgn"].apply(int, base=16)
        for i in range(8):
            tmp[f"{7-i}"] = pd.Series((tmp["data"].apply(int, base=16) // 2**(8*i)) & 0xFF)
        tmp = tmp[tmp["date"] > systemStartTime.strftime("%Y-%m-%d %H:%M:%S")]
        df = df.append(tmp)
        
        
    if(len(df) > 0):
        df = df[df["date"] > (df.iloc[-1, :]["date"] - pd.to_timedelta(f"{maxDisplayTime}s"))]
    
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
    

    fig = make_subplots(rows=4, cols=1, vertical_spacing = 0.065,
                        subplot_titles=["Vehicle Speed [km/h]",
                                        "Accelerator Pedal [%]",
                                        "Engine Speed [rpm]",
                                        "Fuel Consumption [l]"])
    
    fig.append_trace(go.Scatter(x=tachograph["date"], y=tachograph["speed"],
                                name="Vehicle Speed [km/h]", fill="tozeroy"), 1, 1)
    
    fig.append_trace(go.Scatter(x=engineController2["date"], y=engineController2["acceleratorPedal"],
                                name="Accelerator Pedal [%]", fill="tozeroy"), 2, 1)
    
    fig.append_trace(go.Scatter(x=engineController1["date"], y=engineController1["engineSpeed"],
                                name="Engine Speed [rpm]", fill="tozeroy"), 3, 1)
    
    fig.append_trace(go.Scatter(x=fuelConsumption["date"], y=fuelConsumption["fuelConsumption"],
                                name="Fuel Consumption [l]", fill="tozeroy"), 4, 1)

    fig['layout']['xaxis1'].update(range=[min(df["date"]),max(df["date"])], showticklabels=False)
    fig['layout']['xaxis2'].update(range=[min(df["date"]),max(df["date"])], showticklabels=False)
    fig['layout']['xaxis3'].update(range=[min(df["date"]),max(df["date"])], showticklabels=False)
    fig['layout']['xaxis4'].update(range=[min(df["date"]),max(df["date"])])
    
    fig['layout']['yaxis1'].update(range=[0, 265])
    fig['layout']['yaxis2'].update(range=[0, 110])
    fig['layout']['yaxis3'].update(range=[0, 8250])
    fig['layout']['yaxis4'].update(range=[0, max(1, max(fuelConsumption["fuelConsumption"]) * 1.05)])    
    
    fig.update_annotations(font=dict(size=18))
    for i in fig.layout.annotations:
        i.update(x=0.06, yshift=6)
    
    gray = "#CCCCCC"
    fig.update_yaxes(ticks="outside", tickwidth=2, tickcolor='white', ticklen=5,
                     linewidth=1.1, linecolor=gray, gridwidth=1.1, gridcolor=gray,
                     tickfont=dict(size=15))
    fig.update_xaxes(ticks="outside", tickwidth=2, tickcolor='white', ticklen=10,
                     linewidth=1.1, linecolor=gray, gridwidth=1.1, gridcolor=gray,
                     tickfont=dict(size=15))
    
    fig.update_layout(width=1700, height=1100, template="plotly_white")
    fig.update_layout(showlegend=False)
    return fig

update_graph_scatter.fileIndex = -1
update_graph_scatter.time = 0



if __name__ == '__main__':
    serverThread = threading.Thread(target=runServer, daemon=True)
    serverThread.start()
    
    port = 40000
    threading.Timer(1, webbrowser.open_new("http://localhost:{}".format(port))).start();
    app.run_server(port=port)
