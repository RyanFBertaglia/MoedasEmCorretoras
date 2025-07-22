# adicionar array bid para marcar operações em ação
def calc_transaction(coin, corretora_valorizada, corretora_desvalorizada, preco_menor, preco_maior):
    saldos = database.get(coin)

    vender = saldos[corretora_valorizada] * 0.1
    comprar = (vender * preco_maior) / preco_menor
    
    order_sell(vender, corretora_valorizada, coin)
    order_buy(comprar, corretora_desvalorizada, coin)

def order_sell(amount, corretora, coin):
    saldos = database.get(coin)
    saldos[corretora] -= amount
    database.update(coin, saldos)

def order_buy(amount, corretora, coin):
    saldos = database.get(coin)
    saldos[corretora] += amount
    database.update(coin, saldos)