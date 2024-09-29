from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
import asyncio
import logging

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

market_data = {}
connections = set()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("templates/index.html") as f:
        return f.read()

@app.get("/MarketData.html", response_class=HTMLResponse)
async def get_market_data():
    with open("templates/MarketData.html") as f:
        return f.read()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    logger.info(f"WebSocket connection established. Total connections: {len(connections)}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from WebSocket: {data}")
    except WebSocketDisconnect:
        connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(connections)}")

@app.post("/update_market_data")
@app.get("/update_market_data")
async def update_market_data(data: dict = None):
    logger.info(f"Received market data update: {data}")
    if data:
        trader = data["trader"]
        market_data[trader] = {"symbol": data["symbol"], "bid": data["bid"]}
        await broadcast_market_data(data)
        return {"status": "success"}
    return market_data

async def broadcast_market_data(data):
    if connections:
        message = json.dumps({"type": "market_data", "data": data})
        logger.info(f"Broadcasting to {len(connections)} connections: {message}")
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                connections.remove(connection)
    else:
        logger.warning("No WebSocket connections to broadcast to")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")