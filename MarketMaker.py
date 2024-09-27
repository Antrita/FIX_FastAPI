import random
import time

class MarketMaker:
    def __init__(self):
        self.symbols = ["USD/BRL"]
        self.prices = {symbol: random.uniform(4.70, 4.80) for symbol in self.symbols}

    def get_latest_price(self):
        for symbol in self.symbols:
            self.prices[symbol] += random.uniform(-0.02, 0.02)
            self.prices[symbol] = round(max(4.70, min(4.80, self.prices[symbol])), 4)
        return self.symbols[0], self.prices[self.symbols[0]]

def main():
    return MarketMaker()