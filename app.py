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

@app.post("/api/data")
async def receive_data(data: PLCData):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(
        f"[{timestamp}] 🌡️ TEMP: {data.temp}°C | "
        f"💧 HUM: {data.hum}% | "
        f"🌫️ DEW: {data.dew}°C"
    )

    return {"status": "ok", "message": "Dane zapisane"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)