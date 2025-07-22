import requests
import asyncio
import httpx
import time

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

def fetch_all_gateio_tickers(retries=3):
    url = "https://api.gateio.ws/api/v4/spot/tickers"
    for attempt in range(1, retries+1):
        try:
            r = requests.get(url, timeout=10)
            return {item["currency_pair"]: item for item in r.json()}
        except Exception as e:
            print(f"[Gate.io] Tentativa {attempt}: {e}")
            time.sleep(1.5)
    return {}

async def get_all_mexc_asks(symbols, retries=2):
    url_base = "https://api.mexc.com/api/v3/depth?limit=1&symbol="
    asks = {}

    for attempt in range(1, retries+1):
        async with httpx.AsyncClient(timeout=10) as client:
            tasks = [client.get(url_base + symbol) for symbol in symbols]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        all_failed = True
        for symbol, resp in zip(symbols, responses):
            if isinstance(resp, Exception):
                print(f"[MEXC] Tentativa {attempt}: requisição falhou para {symbol}: {resp}")
                asks[symbol] = None
                continue

            if resp.status_code != 200:
                snippet = resp.text[:200].replace("\n", " ")
                print(f"[MEXC] Tentativa {attempt}: status {resp.status_code} para {symbol}: {snippet}")
                asks[symbol] = None
                continue

            try:
                data = resp.json()
            except ValueError:
                snippet = resp.text[:200].replace("\n", " ")
                print(f"[MEXC] Tentativa {attempt}: JSON inválido para {symbol}: '{snippet}'")
                asks[symbol] = None
                continue

            try:
                asks_list = data.get("asks", [])
                ask = float(asks_list[0][0]) if asks_list else None
                asks[symbol] = ask
                if ask is not None:
                    all_failed = False
            except Exception as e:
                print(f"[MEXC] Tentativa {attempt}: parsing do preço para {symbol} falhou: {e}")
                asks[symbol] = None

        if not all_failed:
            break

        await asyncio.sleep(1.5)

    return asks

def fetch_all_data():
    """
    Função principal para obter os dados combinados de Gate.io e MEXC.
    Retorna:
      - gateio_cache: dict com dados da Gate.io
      - mexc_asks: dict com preços ask da MEXC
    """
    gateio_cache = fetch_all_gateio_tickers()
    mexc_symbols = [mexc for _, mexc in PAIRS]
    mexc_asks = asyncio.run(get_all_mexc_asks(mexc_symbols))
    return gateio_cache, mexc_asks
