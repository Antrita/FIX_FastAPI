import sys
import quickfix as fix
import quickfix44 as fix44
import random
import threading
import time
import requests
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import logging
from fastapi.middleware.cors import CORSMiddleware
import json

def gen_order_id():
    return str(random.randint(100000, 999999))

class MarketMaker(fix.Application):
    def __init__(self):
        super().__init__()
        self.running = True
        self.session_id = None
        self.symbols = ["USD/BRL"]
        self.prices = {symbol: random.uniform(100, 1000) for symbol in self.symbols}
        self.subscriptions = set()
        self.fastapi_url = "http://localhost:8000/update_market_data"
        self.orders = {}
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

    '''def handle_new_order(self, message, session_id):
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

        fix.Session.sendToTarget(order, session_id)'''

    def handle_new_order(self, message, session_id):
        order = fix44.ExecutionReport()
        order_id = gen_order_id()
        order.setField(fix.OrderID(order_id))
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

        # Store the order details
        self.orders[order_id] = {
            'clOrdID': clOrdID.getValue(),
            'symbol': symbol.getValue(),
            'side': side.getValue(),
            'orderQty': orderQty.getValue(),
            'status': fix.OrdStatus_NEW
        }

        fix.Session.sendToTarget(order, session_id)

    def get_order_status(self, order_id):
        if order_id in self.orders:
            return self.orders[order_id]
        return None
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
        while self.running:
            for symbol in self.symbols:
                self.prices[symbol] += random.uniform(-0.5, 0.5)
                self.prices[symbol] = max(0.01, self.prices[symbol])
                self.send_update_to_fastapi(symbol)

            for md_req_id in self.subscriptions:
                self.send_market_data(md_req_id, self.session_id)

            time.sleep(5)

    def send_update_to_fastapi(self, symbol):
        data = {
            "symbol": symbol,
            "bid": round(self.prices[symbol] - 0.01, 2),
            "ask": round(self.prices[symbol] + 0.01, 2),
            "trader": "MarketMaker"
        }
        try:
            response = requests.post(self.fastapi_url, json=data)
            if response.status_code != 200:
                print(f"Error sending update to FastAPI: {response.status_code}")
            else:
                print(f"Successfully sent update for {symbol}: {json.dumps(data)}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending update to FastAPI: {e}")

    def start(self):
        settings = fix.SessionSettings("Server.cfg")
        store_factory = fix.FileStoreFactory(settings)
        log_factory = fix.ScreenLogFactory(settings)
        acceptor = fix.SocketAcceptor(self, store_factory, settings, log_factory)

        acceptor.start()