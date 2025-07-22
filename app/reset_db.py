from database import RedisDB

db = RedisDB()
db.client.delete("initialized")
print("Inicialização resetada.")
