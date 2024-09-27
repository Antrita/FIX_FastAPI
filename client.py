import asyncio
import quickfix as fix
import quickfix44 as fix44
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class Client(fix.Application):
    def __init__(self, market_data_queue):
        super().__init__()
        self.sessionID = None
        self.market_data_queue = market_data_queue

    def onCreate(self, sessionID):
        self.sessionID = sessionID
        logging.info(f"onCreate - Session created: {sessionID}")

    def onLogon(self, sessionID):
        logging.info(f"onLogon - Logged on: {sessionID}")

    def onLogout(self, sessionID):
        logging.info(f"onLogout - Logged out: {sessionID}")

    def toAdmin(self, message, sessionID):
        logging.debug(f"toAdmin - Admin message sent: {message}")

    def fromAdmin(self, message, sessionID):
        logging.debug(f"fromAdmin - Admin message received: {message}")

    def toApp(self, message, sessionID):
        logging.debug(f"toApp - Application message sent: {message}")

    def fromApp(self, message, sessionID):
        logging.debug(f"fromApp - Application message received: {message}")
        self.process_message(message)

    def process_message(self, message):
        msgType = fix.MsgType()
        message.getHeader().getField(msgType)

        if msgType.getValue() == fix.MsgType_MarketDataSnapshotFullRefresh:
            self.handle_market_data(message)

    def handle_market_data(self, message):
        symbol = fix.Symbol()
        message.getField(symbol)

        noMDEntries = fix.NoMDEntries()
        message.getField(noMDEntries)

        for i in range(noMDEntries.getValue()):
            group = fix44.MarketDataSnapshotFullRefresh().NoMDEntries()
            message.getGroup(i + 1, group)

            entryType = fix.MDEntryType()
            group.getField(entryType)

            if entryType.getValue() == fix.MDEntryType_BID:
                price = fix.MDEntryPx()
                group.getField(price)
                asyncio.create_task(self.market_data_queue.put({
                    'symbol': symbol.getValue(),
                    'price': price.getValue()
                }))

    async def subscribe_market_data(self, symbol):
        request = fix44.MarketDataRequest()
        request.setField(fix.MDReqID(str(hash(symbol))))
        request.setField(fix.SubscriptionRequestType(fix.SubscriptionRequestType_SNAPSHOT_PLUS_UPDATES))
        request.setField(fix.MarketDepth(0))

        group = fix44.MarketDataRequest().NoMDEntryTypes()
        group.setField(fix.MDEntryType(fix.MDEntryType_BID))
        request.addGroup(group)
        group.setField(fix.MDEntryType(fix.MDEntryType_OFFER))
        request.addGroup(group)

        symbol_group = fix44.MarketDataRequest().NoRelatedSym()
        symbol_group.setField(fix.Symbol(symbol))
        request.addGroup(symbol_group)

        try:
            fix.Session.sendToTarget(request, self.sessionID)
            logging.info(f"Market data subscription requested for {symbol}")
            return True
        except fix.RuntimeError as e:
            logging.error(f"Error subscribing to market data: {e}")
            return False