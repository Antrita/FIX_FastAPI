from datetime import datetime
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel
import asyncio
import json
from pathlib import Path
app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store for market data
market_data = {}

# WebSocket connections
connections = set()

class MarketDataUpdate(BaseModel):
    symbol: str
    bid: float
    ask: float

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("templates/index.html") as f:
        return f.read()

@app.get("/MarketData.html", response_class=HTMLResponse)
async def get_market_data():
    try:
        with open(Path("templates/MarketData.html")) as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="MarketData.html not found")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    finally:
        connections.remove(websocket)

@app.post("/update_market_data")
@app.get("/update_market_data")
async def update_market_data(data: dict = None):
    if data:
        symbol = data["symbol"]
        market_data[symbol] = {"bid": data["bid"], "trader": data["trader"]}
        await broadcast_market_data()
        return {"status": "success"}
    return market_data

async def broadcast_market_data():
    if connections:
        message = {"type": "market_data", "data": market_data}
        await asyncio.gather(
            *[connection.send_json(message) for connection in connections]
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)