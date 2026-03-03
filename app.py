import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# ===== MODEL DANYCH =====
class PLCData(BaseModel):
    temp: float
    hum: float
    dew: float

# ===== TYLKO OSTATNI POMIAR =====
latest_data = {}

# ===== ODBIÓR DANYCH =====
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
        f"[{timestamp}] 🌡️ TEMPERATURA: {data.temp}°C | "
        f"💧 WILGOTNOŚĆ: {data.hum}% | "
        f"🌫️ PUNKT ROSY: {data.dew}°C"
    )

    return {"status": "ok"}

# ===== API DO PODGLĄDU JSON =====
@app.get("/api/data")
async def get_data():
    return latest_data

# ===== DASHBOARD WWW =====
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monitor PLC</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background: #111;
                color: white;
                margin-top: 40px;
            }
            h1 {
                margin-bottom: 40px;
            }
            .box {
                font-size: 36px;
                margin: 25px;
                padding: 20px;
                border-radius: 10px;
                background: #1e1e1e;
                box-shadow: 0 0 15px rgba(0,255,150,0.2);
            }
            .label {
                font-size: 20px;
                color: #aaa;
            }
        </style>
        <script>
            async function fetchData() {
                const response = await fetch('/api/data');
                const data = await response.json();

                if (data.temp !== undefined) {
                    document.getElementById('temp').innerText = data.temp + " °C";
                    document.getElementById('hum').innerText = data.hum + " %";
                    document.getElementById('dew').innerText = data.dew + " °C";
                }
            }

            setInterval(fetchData, 2000);
            window.onload = fetchData;
        </script>
    </head>
    <body>
        <h1>📡 MONITORING PLC</h1>

        <div class="box">
            <div class="label">Temperatura</div>
            <div id="temp">--</div>
        </div>

        <div class="box">
            <div class="label">Wilgotność</div>
            <div id="hum">--</div>
        </div>

        <div class="box">
            <div class="label">Punkt rosy</div>
            <div id="dew">--</div>
        </div>

    </body>
    </html>
    """

# ===== START (Render) =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
