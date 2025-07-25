import requests
import asyncio
import httpx
import time

# Símbolos para Gate.io (spot) e MEXC (futuros)
PAIRS = [
    ("BTC_USDT", "BTC_USDT"),
    ("ETH_USDT", "ETH_USDT"),
    ("DOGE_USDT", "DOGE_USDT"),
    ("SOL_USDT", "SOL_USDT"),
    ("XLM_USDT", "XLM_USDT"),
    ("WHITE_USDT", "WHITE_USDT"),
    ("VVAIFU_USDT", "VVAIFU_USDT"),
    ("ONDO_USDT", "ONDO_USDT"),
    ("ADA_USDT", "ADA_USDT"),
    ("TRX_USDT", "TRX_USDT"),
    ("XRP_USDT", "XRP_USDT"),
    ("LTC_USDT", "LTC_USDT"),
    ("DOT_USDT", "DOT_USDT"),
    ("BNB_USDT", "BNB_USDT"),
    ("AVAX_USDT", "AVAX_USDT"),
    ("LINK_USDT", "LINK_USDT"),
]

def fetch_all_gateio_tickers(retries=3):
    url = "https://api.gateio.ws/api/v4/spot/tickers"
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=10)
            return {item["currency_pair"]: item for item in r.json()}
        except Exception as e:
            print(f"[Gate.io] Tentativa {attempt}: {e}")
            time.sleep(1.5)
    return {}

async def get_all_mexc_asks(symbols, max_attempts=10, delay=1.5):
    url_base = "https://contract.mexc.com/api/v1/contract/depth/"
    asks = {}

    async with httpx.AsyncClient(timeout=10) as client:
        for symbol in symbols:
            attempt = 0
            ask = 0.0

            while attempt < max_attempts:
                attempt += 1
                try:
                    resp = await client.get(url_base + symbol)

                    if resp.status_code != 200:
                        print(f"[MEXC FUTURES] {symbol} tentativa {attempt}: status {resp.status_code}")
                        await asyncio.sleep(delay)
                        continue

                    data = resp.json()
                    asks_list = data.get("data", {}).get("asks", [])

                    if asks_list:
                        ask = float(asks_list[0][0])
                        if ask > 0.0:
                            break

                except Exception as e:
                    print(f"[MEXC FUTURES] {symbol} tentativa {attempt}: erro - {e}")

                await asyncio.sleep(delay)

            asks[symbol] = ask if ask > 0.0 else None

    return asks

def fetch_all_data():
    """
    Função principal para obter os dados combinados de Gate.io (spot) e MEXC (futuros).
    Retorna:
      - gateio_cache: dict com dados da Gate.io
      - mexc_asks: dict com preços ask da MEXC futuros
    """
    gateio_cache = fetch_all_gateio_tickers()
    mexc_symbols = [mexc for _, mexc in PAIRS]
    mexc_asks = asyncio.run(get_all_mexc_asks(mexc_symbols))
    return gateio_cache, mexc_asks
