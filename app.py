import os
import csv
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class PLCData(BaseModel):
    temp: float
    hum: float
    dew: float

latest_data = {}
history = []

ALARM_TEMP = 30

# ===== FUNKCJA ZAPISU DO CSV =====
def save_to_csv(record):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"data_{today}.csv"
    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=';')

        if not file_exists:
            writer.writerow([
                "Data i czas",
                "Temperatura [°C]",
                "Wilgotność [%]",
                "Punkt rosy [°C]"
            ])

        full_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        writer.writerow([
            full_datetime,
            record["temp"],
            record["hum"],
            record["dew"]
        ])

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

    save_to_csv(record)

    return {"status": "ok"}

# ===== HISTORIA =====
@app.get("/api/history")
async def get_history():
    return history

# ===== POBIERANIE PLIKU =====
@app.get("/download")
async def download_file():
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"data_{today}.csv"

    if os.path.isfile(filename):
        return FileResponse(filename, media_type="text/csv", filename=filename)
    return {"error": "Brak pliku"}

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
    background:#0d1117;
    color:white;
    font-family:Arial;
    margin:0;
}

h1 {
    text-align:center;
    padding:20px;
}

.top-bar {
    text-align:center;
    margin-bottom:20px;
}

.top-bar a {
    color:cyan;
    text-decoration:none;
    font-size:16px;
}

.values {
    display:flex;
    justify-content:center;
    gap:30px;
    flex-wrap:wrap;
    margin-bottom:30px;
}

.box {
    background:#161b22;
    padding:18px 30px;
    border-radius:10px;
    font-size:24px;
}

.chart-wrapper {
    max-width:1000px;
    margin:30px auto;
}

canvas {
    width:100% !important;
    height:250px !important;
}
</style>
</head>

<body>

<h1>📡 MONITORING PLC</h1>

<div class="top-bar">
    <a href="/download">⬇ Pobierz dzisiejszy raport CSV</a>
</div>

<div class="values">
    <div class="box">🌡 Temp<br><span id="tempNow">--</span> °C</div>
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

function createChart(id, label, color){
    return new Chart(document.getElementById(id), {
        type:'line',
        data:{ labels:[], datasets:[{
            label:label,
            data:[],
            borderColor:color,
            tension:0.4,
            pointRadius:0
        }]},
        options:{
            responsive:true,
            maintainAspectRatio:false,
            animation:false
        }
    });
}

const tempChart = createChart("tempChart","Temperatura (°C)","lime");
const humChart = createChart("humChart","Wilgotność (%)","cyan");
const dewChart = createChart("dewChart","Punkt rosy (°C)","orange");

async function update(){
    const res = await fetch('/api/history');
    const data = await res.json();
    if(data.length===0) return;

    const labels = data.map(d=>d.time);
    const temps = data.map(d=>d.temp);
    const hums = data.map(d=>d.hum);
    const dews = data.map(d=>d.dew);

    const last = data[data.length-1];

    document.getElementById("tempNow").innerText = last.temp.toFixed(2);
    document.getElementById("humNow").innerText = last.hum.toFixed(2);
    document.getElementById("dewNow").innerText = last.dew.toFixed(2);

    function apply(chart, values){
        chart.data.labels = labels;
        chart.data.datasets[0].data = values;

        const min = Math.min(...values);
        const max = Math.max(...values);
        const buffer = 2;

        chart.options.scales = {
            y: {
                min: min - buffer,
                max: max + buffer
            }
        };

        chart.update();
    }

    apply(tempChart, temps);
    apply(humChart, hums);
    apply(dewChart, dews);
}

setInterval(update,2000);
update();

</script>

</body>
</html>
"""

# ===== START =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)


