import os
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class PLCData(BaseModel):
    temp: float
    hum: float
    dew: float

# 🔥 TYLKO JEDEN REKORD
latest_data = {}

@app.post("/api/data")
async def receive_data(data: PLCData):
    global latest_data

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    latest_data = {
        "time": timestamp,
        "temp": data.temp,
        "hum": data.hum,
        "dew": data.dew
    }

    print(
        f"[{timestamp}] 🌡️ TEMP: {data.temp}°C | "
        f"💧 HUM: {data.hum}% | "
        f"🌫️ DEW: {data.dew}°C"
    )

    return {"status": "ok"}

@app.get("/api/data")
async def get_data():
    return latest_data

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PLC Monitor</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial;
                text-align: center;
                background: #111;
                color: white;
                margin-top: 50px;
            }
            .box {
                font-size: 40px;
                margin: 20px;
            }
        </style>
        <script>
            async function fetchData() {
                const response = await fetch('/api/data');
                const data = await response.json();

                document.getElementById('temp').innerText = data.temp + " °C";
                document.getElementById('hum').innerText = data.hum + " %";
                document.getElementById('dew').innerText = data.dew + " °C";
            }

            setInterval(fetchData, 2000);
            window.onload = fetchData;
        </script>
    </head>
    <body>
        <h1>🌡️ PLC LIVE MONITOR</h1>

        <div class="box">Temp: <span id="temp">--</span></div>
        <div class="box">Hum: <span id="hum">--</span></div>
        <div class="box">Dew: <span id="dew">--</span></div>
    </body>
    </html>
    """
