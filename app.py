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

ALARM_TEMP = 30  # próg alarmu

# ===== ODBIÓR DANYCH =====
@app.post("/api/data")
async def receive_data(data: PLCData):
    global latest_data, history

    now = datetime.now()
    timestamp_str = now.strftime("%H:%M:%S")
    timestamp_raw = now.timestamp()

    record = {
        "time": timestamp_str,
        "temp": round(data.temp, 2),
        "hum": round(data.hum, 2),
        "dew": round(data.dew, 2),
        "timestamp_raw": timestamp_raw
    }

    latest_data = record
    history.append(record)

    if len(history) > 100:
        history.pop(0)

    return {"status": "ok"}

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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitoring PLC</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {
    background: #0d1117;
    color: white;
    font-family: Arial, sans-serif;
    margin: 0;
}

h1 {
    text-align: center;
    padding: 20px;
}

.status {
    text-align: center;
    font-size: 18px;
    margin-bottom: 15px;
}

.online { color: lime; }
.offline { color: red; }

.values {
    display: flex;
    justify-content: center;
    gap: 30px;
    flex-wrap: wrap;
    margin-bottom: 30px;
}

.box {
    background: #161b22;
    padding: 20px 35px;
    border-radius: 10px;
    font-size: 26px;
    box-shadow: 0 0 12px rgba(0,255,150,0.2);
}

.alarm {
    background: #5c0000 !important;
    box-shadow: 0 0 20px red !important;
}

.chart-wrapper {
    max-width: 1100px;
    margin: 40px auto;
}

canvas {
    width: 100% !important;
    height: 280px !important;
}
</style>
</head>

<body>

<h1>📡 MONITORING PLC</h1>

<div class="status">
Status: <span id="statusText" class="offline">OFFLINE</span>
</div>

<div class="values">
    <div class="box" id="tempBox">🌡 Temp<br><span id="tempNow">--</span> °C</div>
    <div class="box">💧 Wilg<br><span id="humNow">--</span> %</div>
    <div class="box">🌫 Rosa<br><span id="dewNow">--</span> °C</div>
</div>

<div class="chart-wrapper">
    <canvas id="tempChart"></canvas>
</div>

<div class="chart-wrapper">
    <canvas id="humChart"></canvas>
</div>

<div class="chart-wrapper">
    <canvas id="dewChart"></canvas>
</div>

<script>

const ALARM_TEMP = 30;

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
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            scales: {
                x: {
                    ticks: { color: '#aaa' },
                    grid: { color: '#222' }
                },
                y: {
                    ticks: { color: '#aaa' },
                    grid: { color: '#222' }
                }
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

    const now = Date.now() / 1000;
    const diff = now - last.timestamp_raw;
    const statusText = document.getElementById("statusText");

    if (diff < 15) {
        statusText.innerText = "ONLINE";
        statusText.className = "online";
    } else {
        statusText.innerText = "OFFLINE";
        statusText.className = "offline";
    }

    const tempBox = document.getElementById("tempBox");
    if (last.temp > ALARM_TEMP) {
        tempBox.classList.add("alarm");
    } else {
        tempBox.classList.remove("alarm");
    }

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
