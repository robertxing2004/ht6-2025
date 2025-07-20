from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/battery-data")
async def battery_data(request: Request):
    data = await request.json()
    print("Received telemetry:", data)
    return {"status": "ok"}
