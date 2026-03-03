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

    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Data", "Godzina", "Temperatura", "Wilgotnosc", "Punkt_Rosy"])

        writer.writerow([
            today,
            record["time"],
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
body { background:#0d1117; color:white; font-family:Arial; margin:0; }
h1 { text-align:center; padding:20px; }
.values { display:flex; justify-content:center; gap:30px; flex-wrap:wrap; margin-bottom:30px; }
.box { background:#161b22; padding:20px 35px; border-radius:10px; font-size:26px; }
.chart-wrapper { max-width:1100px; margin:40px auto; }
canvas { width:100%!important; height:280px!important; }
a { color:cyan; text-decoration:none; font-size:18px; }
</style>
</head>

<body>

<h1>📡 MONITORING PLC</h1>

<div style="text-align:center; margin-bottom:20px;">
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

<script>
const chart = new Chart(document.getElementById('tempChart'), {
    type:'line',
    data:{ labels:[], datasets:[{ label:'Temperatura', data:[], borderColor:'lime', tension:0.4 }] },
    options:{ animation:false }
});

async function update(){
    const res = await fetch('/api/history');
    const data = await res.json();
    if(data.length===0) return;

    const labels = data.map(d=>d.time);
    const temps = data.map(d=>d.temp);

    const last = data[data.length-1];

    document.getElementById("tempNow").innerText = last.temp.toFixed(2);
    document.getElementById("humNow").innerText = last.hum.toFixed(2);
    document.getElementById("dewNow").innerText = last.dew.toFixed(2);

    chart.data.labels = labels;
    chart.data.datasets[0].data = temps;
    chart.update();
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
