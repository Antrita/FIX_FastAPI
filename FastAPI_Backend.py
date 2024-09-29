from datetime import datetime
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel
import asyncio
import json

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
    #A new endpoint that Fetches Bids from a function in MarketMaker
@app.get("/market_data", response_class=HTMLResponse)
async def get_market_data():
    with open("templates/MarketData.html") as f:
        return f.read()

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
async def update_market_data(data: MarketDataUpdate = None):
    if data:
        market_data[data.symbol] = {"bid": data.bid, "ask": data.ask}
        await broadcast_market_data()
        return {"status": "success"}
    else:
        return market_data

async def broadcast_market_data():
    if connections:
        message = json.dumps({"type": "market_data", "data": market_data})
        await asyncio.gather(
            *[connection.send_json({"type": "market_data", "data": market_data}) for connection in connections]
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)