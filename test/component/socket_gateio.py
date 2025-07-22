import time
import json
import threading
import websocket


def on_message(ws, message):
    """
    Called when a message is received from the WebSocket.
    This is where you process your real-time data.
    """
    data = json.loads(message)
    print(f"Raw message received: {json.dumps(data, indent=2)}") # Uncomment to see all raw messages

    if data.get("method") == "spot.tickers":
        ticker_info = data.get("result")
        if ticker_info:
            currency_pair = ticker_info.get("currency_pair")
            highest_bid = ticker_info.get("highest_bid")
            lowest_ask = ticker_info.get("lowest_ask")
            last_price = ticker_info.get("last")

            if currency_pair and highest_bid and lowest_ask and last_price:
                print(f"[{currency_pair}] Bid: {highest_bid}, Ask: {lowest_ask}, Last: {last_price}")

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket connection closed. Status: {close_status_code}, Message: {close_msg}")

def on_open(ws):
    print("WebSocket connection to Gate.io opened.")

    def run(*args):
        subscribe_message = {
            "time": int(time.time()),
            "channel": "spot.tickers",
            "event": "subscribe",
            "payload": ["BTC_USDT", "ETH_USDT"]
        }
        ws.send(json.dumps(subscribe_message))
        print(f"Subscribed to spot.tickers for BTC_USDT and ETH_USDT.")
    threading.Thread(target=run).start()

def connect_gateio_websocket():
    websocket_url = "wss://api.gateio.ws/ws/v4/"

    ws = websocket.WebSocketApp(
        websocket_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    print("Starting WebSocket connection...")
    ws.run_forever()

if __name__ == "__main__":
    connect_gateio_websocket()