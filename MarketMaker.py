import sys
import quickfix as fix
import quickfix44 as fix44
import random
import threading
import time
import requests
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def gen_order_id():
    return str(random.randint(100000, 999999))

class MarketMaker(fix.Application):
    def __init__(self):
        super().__init__()
        self.session_id = None
        self.symbols = ["USD/BRL"]
        self.prices = {symbol: random.uniform(100, 1000) for symbol in self.symbols}
        self.subscriptions = set()
        self.fastapi_url = "http://localhost:8000/update_market_data"
        self.running = True

    def onCreate(self, session_id):
        self.session_id = session_id
        logger.info(f"Session created - {session_id}")

    def onLogon(self, session_id):
        logger.info(f"Logon - {session_id}")

    def onLogout(self, session_id):
        logger.info(f"Logout - {session_id}")

    def toAdmin(self, message, session_id):
        pass

    def fromAdmin(self, message, session_id):
        pass

    def toApp(self, message, session_id):
        logger.info(f"Sending message: {message}")

    def fromApp(self, message, session_id):
        logger.info(f"Received message: {message}")
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)

        if msgType.getValue() == fix.MsgType_NewOrderSingle:
            self.handle_new_order(message, session_id)
        elif msgType.getValue() == fix.MsgType_OrderCancelRequest:
            self.handle_cancel_request(message, session_id)
        elif msgType.getValue() == fix.MsgType_MarketDataRequest:
            self.handle_market_data_request(message, session_id)

    def handle_new_order(self, message, session_id):
        order = fix44.ExecutionReport()
        order.setField(fix.OrderID(gen_order_id()))
        order.setField(fix.ExecID(gen_order_id()))
        order.setField(fix.ExecType(fix.ExecType_NEW))
        order.setField(fix.OrdStatus(fix.OrdStatus_NEW))

        clOrdID = fix.ClOrdID()
        symbol = fix.Symbol()
        side = fix.Side()
        orderQty = fix.OrderQty()

        message.getField(clOrdID)
        message.getField(symbol)
        message.getField(side)
        message.getField(orderQty)

        order.setField(clOrdID)
        order.setField(symbol)
        order.setField(side)
        order.setField(orderQty)
        order.setField(fix.LastQty(orderQty.getValue()))
        order.setField(fix.LastPx(self.prices[symbol.getValue()]))
        order.setField(fix.CumQty(orderQty.getValue()))
        order.setField(fix.AvgPx(self.prices[symbol.getValue()]))

        fix.Session.sendToTarget(order, session_id)

    def handle_cancel_request(self, message, session_id):
        cancel = fix44.OrderCancelReject()
        cancel.setField(fix.OrderID(gen_order_id()))
        cancel.setField(fix.ClOrdID(gen_order_id()))
        cancel.setField(fix.OrigClOrdID(message.getField(fix.OrigClOrdID())))
        cancel.setField(fix.OrdStatus(fix.OrdStatus_REJECTED))
        cancel.setField(fix.CxlRejResponseTo(fix.CxlRejResponseTo_ORDER_CANCEL_REQUEST))
        cancel.setField(fix.CxlRejReason(fix.CxlRejReason_OTHER))

        fix.Session.sendToTarget(cancel, session_id)

    def handle_market_data_request(self, message, session_id):
        mdReqID = fix.MDReqID()
        subscriptionRequestType = fix.SubscriptionRequestType()
        message.getField(mdReqID)
        message.getField(subscriptionRequestType)

        if subscriptionRequestType.getValue() == fix.SubscriptionRequestType_SNAPSHOT_PLUS_UPDATES:
            self.subscriptions.add(mdReqID.getValue())
            self.send_market_data(mdReqID.getValue(), session_id)
        elif subscriptionRequestType.getValue() == fix.SubscriptionRequestType_DISABLE_PREVIOUS_SNAPSHOT_PLUS_UPDATE_REQUEST:
            self.subscriptions.remove(mdReqID.getValue())

    def send_market_data(self, md_req_id, session_id):
        for symbol in self.symbols:
            snapshot = fix44.MarketDataSnapshotFullRefresh()
            snapshot.setField(fix.MDReqID(md_req_id))
            snapshot.setField(fix.Symbol(symbol))

            group = fix44.MarketDataSnapshotFullRefresh().NoMDEntries()
            group.setField(fix.MDEntryType(fix.MDEntryType_BID))
            group.setField(fix.MDEntryPx(self.prices[symbol] - 0.01))
            group.setField(fix.MDEntrySize(100))
            snapshot.addGroup(group)

            group.setField(fix.MDEntryType(fix.MDEntryType_OFFER))
            group.setField(fix.MDEntryPx(self.prices[symbol] + 0.01))
            group.setField(fix.MDEntrySize(100))
            snapshot.addGroup(group)

            fix.Session.sendToTarget(snapshot, session_id)

    def stream_bids(self):
        trader = "Trader"
        while self.running:
            try:
                for symbol in self.symbols:
                    bid = round(self.prices[symbol] + random.uniform(-0.5, 0.5), 2)
                    data = {
                        "symbol": symbol,
                        "bid": bid,
                        "trader": trader
                    }
                    logger.info(f"Preparing to send bid: {data}")
                    try:
                        response = requests.post(self.fastapi_url, json=data)
                        logger.info(f"Bid sent. Response status: {response.status_code}")
                        if response.status_code != 200:
                            logger.error(f"Failed to send bid. Response: {response.text}")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Error sending bid to FastAPI: {e}")
                time.sleep(4)  # Stream new bids every 4 seconds
            except Exception as e:
                logger.error(f"Error in stream_bids: {e}")
                time.sleep(5)  # Wait a bit before retrying if there's an error

    def start(self):
        settings = fix.SessionSettings("Server.cfg")
        store_factory = fix.FileStoreFactory(settings)
        log_factory = fix.ScreenLogFactory(settings)
        acceptor = fix.SocketAcceptor(self, store_factory, settings, log_factory)

        acceptor.start()

        # Start the bid streaming thread
        threading.Thread(target=self.stream_bids, daemon=True).start()

    def stop(self):
        self.running = False

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store for market data
market_data = {}

# WebSocket connections
connections = []

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
    connections.append(websocket)
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
    return market_data

async def broadcast_market_data():
    if connections:
        message = {"type": "market_data", "data": market_data}
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                connections.remove(connection)

def run_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def run_market_maker(application):
    try:
        application.start()
        while application.running:
            time.sleep(1)
    except (fix.ConfigError, fix.RuntimeError) as e:
        logger.error(f"Error in market maker thread: {e}")
    finally:
        application.stop()

def main():
    try:
        application = MarketMaker()

        # FastAPI thread
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()

        # MarketMaker thread
        market_maker_thread = threading.Thread(target=run_market_maker, args=(application,), daemon=True)
        market_maker_thread.start()

        logger.info("Market Maker, FastAPI server, and Bid Streaming started.")

        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        application.stop()
    except Exception as e:
        logger.error(f"Error in main thread: {e}")
    finally:
        logger.info("MarketMaker shut down.")

if __name__ == "__main__":
    main()