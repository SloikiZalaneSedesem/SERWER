from fastapi.responses import HTMLResponse

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
