import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn
import quickfix as fix
from typing import List
from client import Client
from MarketMaker import main as start_market_maker

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# Initialize MarketMaker
market_maker = start_market_maker()

# Initialize QuickFIX and Client
settings = fix.SessionSettings("client.cfg")
store_factory = fix.FileStoreFactory(settings)
log_factory = fix.ScreenLogFactory(settings)
market_data_queue = asyncio.Queue()
client = Client(market_data_queue)
initiator = fix.SocketInitiator(client, store_factory, settings, log_factory)

@app.on_event("startup")
async def startup_event():
    # Start QuickFIX initiator
    initiator.start()

@app.on_event("shutdown")
async def shutdown_event():
    # Stop QuickFIX initiator
    initiator.stop()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data['action'] == 'subscribe':
                await client.subscribe_market_data(data['symbol'])
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_market_data():
    while True:
        market_data = await market_data_queue.get()
        for connection in active_connections:
            await connection.send_json(market_data)

@app.get("/")
async def get():
    return {"message": "FIX Client is running"}

# Start the market data broadcasting task
@app.on_event("startup")
async def start_market_data_broadcast():
    asyncio.create_task(broadcast_market_data())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)