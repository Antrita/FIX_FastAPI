import uvicorn
from fastapi_app import app
from MarketMaker import MarketMaker
import threading
import time

def run_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def run_market_maker(application):
    try:
        application.start()
        # Start the price updating immediately
        application.update_prices()
    except Exception as e:
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

if __name__ == "__main__":
    main()