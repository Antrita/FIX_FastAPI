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

    def onCreate(self, session_id):
        self.session_id = session_id
        print(f"Session created - {session_id}")

    def onLogon(self, session_id):
        print(f"Logon - {session_id}")

    def onLogout(self, session_id):
        print(f"Logout - {session_id}")

    def toAdmin(self, message, session_id):
        pass

    def fromAdmin(self, message, session_id):
        pass

    def toApp(self, message, session_id):
        print(f"Sending message: {message}")

    def fromApp(self, message, session_id):
        print(f"Received message: {message}")
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

    def update_prices(self):
        while True:
            for symbol in self.symbols:
                self.prices[symbol] += random.uniform(-0.5, 0.5)
                self.prices[symbol] = max(0.01, self.prices[symbol])
                self.send_update_to_fastapi(symbol)

            for md_req_id in self.subscriptions:
                self.send_market_data(md_req_id, self.session_id)

            time.sleep(1)

    def send_update_to_fastapi(self, symbol):
        data = {
            "symbol": symbol,
            "bid": round(self.prices[symbol] - 0.01, 2),
            "ask": round(self.prices[symbol] + 0.01, 2)
        }
        try:
            requests.post(self.fastapi_url, json=data)
        except requests.exceptions.RequestException as e:
            print(f"Error sending update to FastAPI: {e}")

    def start(self):
        settings = fix.SessionSettings("Server.cfg")
        store_factory = fix.FileStoreFactory(settings)
        log_factory = fix.ScreenLogFactory(settings)
        acceptor = fix.SocketAcceptor(self, store_factory, settings, log_factory)

        acceptor.start()

        # Start the price updating thread
        threading.Thread(target=self.update_prices, daemon=True).start()

# FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store for market data
market_data = {}

# WebSocket connections
connections = set()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("templates/index.html") as f:
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
async def update_market_data(data: dict):
    symbol = data["symbol"]
    market_data[symbol] = {"bid": data["bid"], "ask": data["ask"]}
    await broadcast_market_data()
    return {"status": "success"}

async def broadcast_market_data():
    if connections:
        message = {"type": "market_data", "data": market_data}
        await asyncio.gather(
            *[connection.send_json(message) for connection in connections]
        )

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def run_market_maker(application):
    try:
        application.start()
        while True:
            time.sleep(1)
    except (fix.ConfigError, fix.RuntimeError) as e:
        print(f"Error in market maker thread: {e}")


def main():
    try:
        application = MarketMaker()

        # Start FastAPI in a separate thread
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()

        # Start MarketMaker in a separate thread
        market_maker_thread = threading.Thread(target=run_market_maker, args=(application,), daemon=True)
        market_maker_thread.start()

        print("Market Maker and FastAPI server started.")

        # Keep the main thread running
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Error in main thread: {e}")
        sys.exit()


if __name__ == "__main__":
    main()