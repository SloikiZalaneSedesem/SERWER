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

# ===== ODBIÓR DANYCH =====
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

    # trzymamy tylko ostatnie 100 pomiarów
    if len(history) > 100:
        history.pop(0)

    print(f"[{timestamp}] TEMP: {data.temp}°C")

    return {"status": "ok"}

# ===== AKTUALNE DANE =====
@app.get("/api/data")
async def get_data():
    return latest_data

# ===== HISTORIA =====
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
                font-family: Arial, sans-serif;
                text-align: center;
                background: #111;
                color: white;
            }
            h1 {
                margin-top: 20px;
            }
            .current {
                font-size: 26px;
                margin: 20px;
            }
            canvas {
                max-width: 95%;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>

        <h1>📡 MONITORING PLC</h1>

        <div class="current">
            🌡 Temperatura: <span id="tempNow">--</span> °C |
            💧 Wilgotność: <span id="humNow">--</span> % |
            🌫 Punkt rosy: <span id="dewNow">--</span> °C
        </div>

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
                        tension: 0.4,
                        pointRadius: 2
                    }]
                },
                options: {
                    responsive: true,
                    animation: false,
                    scales: {
                        x: {
                            ticks: { color: 'white' }
                        },
                        y: {
                            ticks: { color: 'white' }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: { color: 'white' }
                        }
                    }
                }
            });

            async function updateChart() {
                const response = await fetch('/api/history');
                const data = await response.json();

                const temps = data.map(d => d.temp);
                const labels = data.map(d => d.time);

                chart.data.labels = labels;
                chart.data.datasets[0].data = temps;

                if (data.length > 0) {
                    const last = data[data.length - 1];

                    document.getElementById("tempNow").innerText = last.temp;
                    document.getElementById("humNow").innerText = last.hum;
                    document.getElementById("dewNow").innerText = last.dew;

                    const minTemp = Math.min(...temps);
                    const maxTemp = Math.max(...temps);
                    const buffer = 2;

                    chart.options.scales.y.min = minTemp - buffer;
                    chart.options.scales.y.max = maxTemp + buffer;
                }

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
