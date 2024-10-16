from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import json
app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store for market data
market_data = {}

# WebSocket connections
connections = set()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("templates/index.html") as f:
        return f.read()

@app.get("/MarketData.html", response_class=FileResponse)
async def get_market_data():
    file_path = "templates/MarketData.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        logger.error(f"MarketData.html not found at {os.path.abspath(file_path)}")
        raise HTTPException(status_code=404, detail="MarketData.html not found")

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
async def update_market_data(data: dict):
    if "symbol" in data:
        symbol = data["symbol"]
        market_data[symbol] = data
        await broadcast_market_data({symbol: data})
        return {"status": "success"}
    return {"status": "error", "message": "Invalid data provided"}

@app.get("/update_market_data")
async def update_market_data(data: dict = None):
    if data and "symbol" in data:
        symbol = data["symbol"]
        market_data[symbol] = data
        await broadcast_market_data({symbol: data})
        return {"status": "success"}
    return {"status": "error", "message": "Invalid data provided"}

@app.post("/check_order_status")
async def check_order_status(order_id: str):
    if hasattr(app, 'market_maker'):
        status = app.market_maker.get_order_status(order_id)
        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    else:
        raise HTTPException(status_code=500, detail="MarketMaker not initialized")
@app.get("/get_current_market_price/{symbol}")
async def get_current_market_price(symbol: str):
    if hasattr(app, 'market_maker'):
        price = app.market_maker.get_current_market_price(symbol)
        if price is not None:
            return {"symbol": symbol, "price": price}
        else:
            raise HTTPException(status_code=404, detail="Symbol not found")
    else:
        raise HTTPException(status_code=500, detail="MarketMaker not initialized")
async def broadcast_market_data(data):
    if connections:
        message = json.dumps({"type": "market_data", "data": data})
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                connections.remove(connection)