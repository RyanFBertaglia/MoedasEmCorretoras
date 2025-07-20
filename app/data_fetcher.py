import threading
import time
import requests
from typing import Dict, Any

data_store: Dict[str, Any] = {}
_lock = threading.Lock()

PAIRS = [
    ("BTC_USDT", "BTCUSDT"),
    ("ETH_USDT", "ETHUSDT"),
    ("DOGE_USDT", "DOGEUSDT"),
    ("SOL_USDT", "SOLUSDT"),
    ("LAI_USDT", "LAIUSDT"),
    ("FIL_USDT", "FILUSDT"),
    ("XLM_USDT", "XLMUSDT"),
    ("WHITE_USDT", "WHITEUSDT"),
    ("VVAIFU_USDT", "VVAIFUUSDT"),
    ("ONDO_USDT", "ONDOUSDT"),
    ("ADA_USDT", "ADAUSDT"),
    ("TRX_USDT", "TRXUSDT"),
    ("XRP_USDT", "XRPUSDT"),
    ("LTC_USDT", "LTCUSDT"),
    ("DOT_USDT", "DOTUSDT"),
    ("BNB_USDT", "BNBUSDT"),
    ("AVAX_USDT", "AVAXUSDT"),
    ("LINK_USDT", "LINKUSDT"),
]

FETCH_INTERVAL = 0.5

def _fetch_gateio():
    url = "https://api.gateio.ws/api/v4/spot/tickers"
    while True:
        for gate_sym, _ in PAIRS:
            try:
                r = requests.get(url, params={"currency_pair": gate_sym}, timeout=5)
                arr = r.json()
                bid = float(arr[0].get("highest_bid", 0)) if arr else None
            except Exception:
                bid = None

            with _lock:
                data_store[gate_sym + "_bid"] = bid
        time.sleep(FETCH_INTERVAL)

def _fetch_mexc():
    url = "https://api.mexc.com/api/v3/depth"
    while True:
        for _, mexc_sym in PAIRS:
            try:
                r = requests.get(url, params={"symbol": mexc_sym, "limit": 1}, timeout=5)
                d = r.json()
                ask = float(d["asks"][0][0]) if d.get("asks") else None
            except Exception:
                ask = None

            with _lock:
                data_store[mexc_sym + "_ask"] = ask
        time.sleep(FETCH_INTERVAL)

def start_background_fetch():
    t1 = threading.Thread(target=_fetch_gateio, daemon=True, name="fetch_gateio")
    t2 = threading.Thread(target=_fetch_mexc, daemon=True, name="fetch_mexc")
    t1.start()
    t2.start()

def get_pair_data(gate_sym: str, mexc_sym: str):
    with _lock:
        bid = data_store.get(gate_sym + "_bid")
        ask = data_store.get(mexc_sym + "_ask")
    return bid, ask