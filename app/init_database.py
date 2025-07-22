from database import RedisDB
from data_fetcher import fetch_all_data, PAIRS

db = RedisDB()

def init_balances():
    print("Consultando preços nas corretoras...")
    gateio_data, mexc_asks = fetch_all_data()

    for pair_gate, pair_mexc in PAIRS:
        coin = pair_gate.split("_")[0].upper()

        gate_price = None
        gate_data = gateio_data.get(pair_gate)
        if gate_data:
            try:
                gate_price = float(gate_data["last"])
            except (KeyError, ValueError):
                print(f"[Gate.io] Erro ao converter preço para {pair_gate}")

        mexc_price = None
        try:
            mexc_price = float(mexc_asks.get(pair_mexc)) if mexc_asks.get(pair_mexc) else None
        except (TypeError, ValueError):
            print(f"[MEXC] Erro ao converter preço para {pair_mexc}")

        # 100 USD -> Moeda x
        gate_qty = round(100 / gate_price, 8) if gate_price else 0.0
        mexc_qty = round(100 / mexc_price, 8) if mexc_price else 0.0

        balances = {
            "gateio": gate_qty,
            "mexc": mexc_qty
        }

        db.init_coin(coin, balances)
        print(f"[{coin}] gateio: {gate_qty}, mexc: {mexc_qty}")

if __name__ == "__main__":
    init_balances()
