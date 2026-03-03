import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# ===== MODEL =====
class PLCData(BaseModel):
    temp: float
    hum: float
    dew: float

# ===== DANE =====
latest_data = {}
history = []

# ===== POST =====
@app.post("/api/data")
async def receive_data(data: PLCData):
    global latest_data, history

    timestamp = datetime.now().strftime("%H:%M:%S")

    record = {
        "time": timestamp,
        "temp": data.temp,
        "hum": data.hum,
        "dew": data.dew
    }

    latest_data = record
    history.append(record)

    if len(history) > 100:
        history.pop(0)

    print(f"[{timestamp}] TEMP: {data.temp}°C")

    return {"status": "ok"}

# ===== GET AKTUALNE =====
@app.get("/api/data")
async def get_data():
    return latest_data

# ===== GET HISTORIA =====
@app.get("/api/history")
async def get_history():
    return history

# ===== DASHBOARD =====
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Monitor PLC</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: Arial;
                text-align: center;
                background: #111;
                color: white;
            }
            canvas {
                max-width: 90%;
                margin-top: 40px;
            }
        </style>
    </head>
    <body>

        <h1>📈 Wykres Temperatury</h1>
        <canvas id="tempChart"></canvas>

        <script>
            const ctx = document.getElementById('tempChart').getContext('2d');

            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Temperatura (°C)',
                        data: [],
                        borderColor: 'lime',
                        borderWidth: 2,
                        tension: 0.2
                    }]
                },
                options: {
                    scales: {
                        x: { ticks: { color: 'white' } },
                        y: { ticks: { color: 'white' } }
                    },
                    plugins: {
                        legend: { labels: { color: 'white' } }
                    }
                }
            });

            async function updateChart() {
                const response = await fetch('/api/history');
                const data = await response.json();

                chart.data.labels = data.map(d => d.time);
                chart.data.datasets[0].data = data.map(d => d.temp);
                chart.update();
            }

            setInterval(updateChart, 2000);
            updateChart();
        </script>

    </body>
    </html>
    """

# ===== START =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
