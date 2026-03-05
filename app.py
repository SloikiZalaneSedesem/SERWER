import sqlite3
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()

DB_NAME = "data.db"
ALARM_TEMP = 30


# =========================
# INICJALIZACJA BAZY
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temp REAL,
            hum REAL,
            dew REAL
        )
    """)
    conn.commit()
    conn.close()


init_db()


# =========================
# MODEL DANYCH
# =========================
class PLCData(BaseModel):
    temp: float
    hum: float
    dew: float


# =========================
# ZAPIS DO BAZY
# =========================
@app.post("/api/data")
async def receive_data(data: PLCData):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO measurements (timestamp, temp, hum, dew)
        VALUES (?, ?, ?, ?)
    """, (timestamp, data.temp, data.hum, data.dew))

    conn.commit()
    conn.close()

    return {"status": "ok"}


# =========================
# POBIERANIE HISTORII Z ZAKRESEM CZASU
# =========================
@app.get("/api/history")
async def get_history(hours: int = 1):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, temp, hum, dew
        FROM measurements
        WHERE timestamp >= datetime('now', ?)
        ORDER BY timestamp ASC
    """, (f"-{hours} hours",))

    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "time": row[0].split(" ")[1],
            "temp": row[1],
            "hum": row[2],
            "dew": row[3]
        })

    return data


# =========================
# DASHBOARD
# =========================
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitoring PLC (SQLite)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body { background:#111; color:white; font-family:Arial; text-align:center; }
h1 { margin-top:20px; }
.values { margin:20px; }
.box { padding:15px 25px; margin:10px; display:inline-block; background:#222; border-radius:8px; transition:0.3s; }
.alarm { background:#5c0000 !important; box-shadow:0 0 15px red; }
.chart { max-width:900px; margin:30px auto; }
canvas { height:250px !important; }
button { padding:8px 15px; margin:5px; cursor:pointer; }
</style>
</head>

<body>

<h1>Monitoring PLC (SQLite)</h1>

<div>
    <button onclick="setRange(1)">1h</button>
    <button onclick="setRange(6)">6h</button>
    <button onclick="setRange(24)">24h</button>
</div>

<div class="values">
    <div class="box" id="tempBox">🌡 Temp: <span id="tempNow">--</span> °C</div>
    <div class="box">💧 Wilg: <span id="humNow">--</span> %</div>
    <div class="box">🌫 Rosa: <span id="dewNow">--</span> °C</div>
</div>

<div class="chart"><canvas id="tempChart"></canvas></div>
<div class="chart"><canvas id="humChart"></canvas></div>
<div class="chart"><canvas id="dewChart"></canvas></div>

<script>

let currentHours = 1;

function setRange(hours){
    currentHours = hours;
    update();
}

function createChart(id,label,color){
    return new Chart(document.getElementById(id),{
        type:'line',
        data:{labels:[],datasets:[{label:label,data:[],borderColor:color,tension:0.4,pointRadius:0}]},
        options:{responsive:true,maintainAspectRatio:false,animation:false}
    });
}

const tempChart=createChart("tempChart","Temperatura","lime");
const humChart=createChart("humChart","Wilgotność","cyan");
const dewChart=createChart("dewChart","Punkt rosy","orange");

async function update(){
    const res = await fetch('/api/history?hours=' + currentHours);
    const data = await res.json();
    if(data.length === 0) return;

    const labels = data.map(d => d.time);
    const temps = data.map(d => d.temp);
    const hums = data.map(d => d.hum);
    const dews = data.map(d => d.dew);

    const last = data[data.length-1];

    document.getElementById("tempNow").innerText = last.temp.toFixed(2);
    document.getElementById("humNow").innerText = last.hum.toFixed(2);
    document.getElementById("dewNow").innerText = last.dew.toFixed(2);

    const tempBox = document.getElementById("tempBox");
    if(last.temp > 30){
        tempBox.classList.add("alarm");
    } else {
        tempBox.classList.remove("alarm");
    }

    function apply(chart, values){
        chart.data.labels = labels;
        chart.data.datasets[0].data = values;
        chart.update();
    }

    apply(tempChart, temps);
    apply(humChart, hums);
    apply(dewChart, dews);
}

setInterval(update, 10000);
update();

</script>

</body>
</html>
"""


# =========================
# START
# =========================
if __name__ == "__main__":
    port = int(__import__("os").environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
