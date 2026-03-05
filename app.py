import os
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
# MODEL
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
# POBIERANIE DANYCH (ostatnia godzina)
# =========================
@app.get("/api/history")
async def get_history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, temp, hum, dew
        FROM measurements
        ORDER BY id DESC
        LIMIT 360
    """)

    rows = cursor.fetchall()
    conn.close()

    # odwracamy żeby były rosnąco
    rows.reverse()

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
<title>Monitoring PLC</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body { background:#111; color:white; font-family:Arial; text-align:center; }
.chart { max-width:900px; margin:30px auto; }
canvas { height:250px !important; }
.box { padding:15px; margin:10px; display:inline-block; background:#222; border-radius:8px; }
.alarm { background:#5c0000 !important; }
</style>
</head>

<body>

<h1>Monitoring PLC (SQLite)</h1>

<div class="box" id="tempBox">Temp: <span id="tempNow">--</span> °C</div>
<div class="box">Wilg: <span id="humNow">--</span> %</div>
<div class="box">Rosa: <span id="dewNow">--</span> °C</div>

<div class="chart"><canvas id="tempChart"></canvas></div>

<script>
const chart = new Chart(document.getElementById('tempChart'), {
    type:'line',
    data:{labels:[], datasets:[{label:'Temp', data:[], borderColor:'lime'}]},
    options:{animation:false}
});

async function update(){
    const res = await fetch('/api/history');
    const data = await res.json();
    if(data.length === 0) return;

    const labels = data.map(d => d.time);
    const temps = data.map(d => d.temp);

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

    chart.data.labels = labels;
    chart.data.datasets[0].data = temps;
    chart.update();
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
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
