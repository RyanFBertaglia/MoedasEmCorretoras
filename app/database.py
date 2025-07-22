import redis
from redis.commands.json.path import Path

class RedisDB:
    def __init__(self):
        self._client = redis.Redis(
            host="localhost",
            port=6379,
            db=0,
            decode_responses=True
        )
        self.PREFIX = "arb:balances:"

    def init_coin(self, coin: str, initial_balances: dict):
        key = self.PREFIX + coin
        self._client.json().set(key, Path.root_path(), initial_balances)

    def get(self, coin: str) -> dict:
        key = self.PREFIX + coin
        data = self._client.json().get(key)
        return data or {}

    def set(self, key, value):
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        self._client.set(key, value)


    def update(self, coin: str, balances: dict):
        key = self.PREFIX + coin
        self._client.json().set(key, Path.root_path(), balances)

    def incr(self, coin: str, exchange: str, amount: float):
        key = self.PREFIX + coin
        path = Path(f"$.{exchange}")
        self._client.json().numincrby(key, path, amount)

if __name__ == "__main__":
    db = RedisDB()
    db.init_coin("BTC", {"gateio": 100.0, "mexc": 100.0})
    print("Saldos iniciais:", db.get("BTC"))
    db.incr("BTC", "gateio", 5)
    print("Depois do incremento:", db.get("BTC"))
