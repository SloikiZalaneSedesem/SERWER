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
        "temp": round(data.temp, 2),
        "hum": round(data.hum, 2),
        "dew": round(data.dew, 2)
    }

    latest_data = record
    history.append(record)

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
    <title>Monitoring PLC</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
            text-align: center;
        }
        h1 {
            margin-top: 20px;
        }
        .values {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 30px;
            margin: 30px 0;
        }
        .box {
            background: #1e1e1e;
            padding: 20px 30px;
            border-radius: 10px;
            font-size: 28px;
            box-shadow: 0 0 10px rgba(0,255,150,0.3);
        }
        canvas {
            max-width: 95%;
            margin: 40px auto;
        }
    </style>
</head>
<body>

    <h1>📡 MONITORING PLC</h1>

    <div class="values">
        <div class="box">🌡 Temperatura<br><span id="tempNow">--</span> °C</div>
        <div class="box">💧 Wilgotność<br><span id="humNow">--</span> %</div>
        <div class="box">🌫 Punkt rosy<br><span id="dewNow">--</span> °C</div>
    </div>

    <canvas id="tempChart"></canvas>
    <canvas id="humChart"></canvas>
    <canvas id="dewChart"></canvas>

<script>
function createChart(canvasId, label, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: color,
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 1
            }]
        },
        options: {
            responsive: true,
            animation: false,
            scales: {
                x: { ticks: { color: 'white' } },
                y: { ticks: { color: 'white' } }
            },
            plugins: {
                legend: { labels: { color: 'white' } }
            }
        }
    });
}

const tempChart = createChart("tempChart", "Temperatura (°C)", "lime");
const humChart = createChart("humChart", "Wilgotność (%)", "cyan");
const dewChart = createChart("dewChart", "Punkt rosy (°C)", "orange");

async function updateCharts() {
    const response = await fetch('/api/history');
    const data = await response.json();

    if (data.length === 0) return;

    const labels = data.map(d => d.time);
    const temps = data.map(d => d.temp);
    const hums = data.map(d => d.hum);
    const dews = data.map(d => d.dew);

    const last = data[data.length - 1];

    document.getElementById("tempNow").innerText = last.temp.toFixed(2);
    document.getElementById("humNow").innerText = last.hum.toFixed(2);
    document.getElementById("dewNow").innerText = last.dew.toFixed(2);

    function updateChart(chart, values) {
        chart.data.labels = labels;
        chart.data.datasets[0].data = values;

        const min = Math.min(...values);
        const max = Math.max(...values);
        const buffer = 2;

        chart.options.scales.y.min = min - buffer;
        chart.options.scales.y.max = max + buffer;

        chart.update();
    }

    updateChart(tempChart, temps);
    updateChart(humChart, hums);
    updateChart(dewChart, dews);
}

setInterval(updateCharts, 2000);
updateCharts();

</script>

</body>
</html>
"""

# ===== START =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
