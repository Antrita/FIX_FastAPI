import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import uvicorn
import quickfix as fix
from typing import List

app = FastAPI()

# Serve static files (your JavaScript UI)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# QuickFIX application class
class QuickFixApplication(fix.Application):
    def onCreate(self, sessionID):
        print("Session created:", sessionID)

    def onLogon(self, sessionID):
        print("Logon:", sessionID)

    def onLogout(self, sessionID):
        print("Logout:", sessionID)

    def fromAdmin(self, message, sessionID):
        pass

    def toAdmin(self, message, sessionID):
        pass

    def fromApp(self, message, sessionID):
        print("FromApp:", message)
        # When a message is received, send it to all active WebSocket connections
        asyncio.create_task(broadcast_message(str(message)))

    def toApp(self, message, sessionID):
        print("ToApp:", message)

# Initialize QuickFIX
settings = fix.SessionSettings("quickfix.cfg")
application = QuickFixApplication()
storeFactory = fix.FileStoreFactory(settings)
logFactory = fix.ScreenLogFactory(settings)
initiator = fix.SocketInitiator(application, storeFactory, settings, logFactory)

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
            # Wait for any message from the client
            data = await websocket.receive_text()
            # You can process the received data here if needed
    except:
        active_connections.remove(websocket)

async def broadcast_message(message: str):
    for connection in active_connections:
        await connection.send_text(message)

@app.get("/")
async def get():
    return {"message": "FIX Client is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)