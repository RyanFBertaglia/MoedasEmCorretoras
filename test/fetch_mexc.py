import threading
import requests
import time
from typing import Dict, Any

_order_book_lock = threading.Lock()
_order_book: Dict[str, Any] = {}

def get_current_order_book() -> Dict[str, Any]:
    with _order_book_lock:
        return _order_book.copy()

def update_order_book_data(symbol: str = "BTCUSDT", interval: int = 1):
    while True:
        try:
            url = "https://api.mexc.com/api/v3/depth"
            params = {"symbol": symbol, "limit": 1}

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            best_ask = data.get("asks", [])[0] if data.get("asks") else []

            with _order_book_lock:
                _order_book.clear()
                _order_book.update({
                    "ask_price": best_ask[0] if best_ask else None
                })

        except Exception as e:
            print(f"Erro ao atualizar order book: {e}")
        finally:
            time.sleep(interval)

# Inicia a thread automaticamente
threading.Thread(target=update_order_book_data, daemon=True, name="MEXC_OrderBook_Updater").start()
