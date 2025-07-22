import streamlit as st
import numpy as np
from streamlit_autorefresh import st_autorefresh
import data_fetcher

from database import RedisDB
db = RedisDB()


st.set_page_config(page_title="Arbitragem Multi-Moeda REST", layout="wide")

if "spread_history" not in st.session_state:
    st.session_state.spread_history = {}
if "active_trades" not in st.session_state:
    st.session_state.active_trades = {}

col1, col2, col3 = st.columns(3)
with col1:
    refresh_rate = st.slider("⏱ Atualizar a cada (segundos):", 5, 30, 10)
with col2:
    alert_threshold = st.slider("⚠️ Alerta se Spread % >", 0.1, 5.0, 1.5)
with col3:
    sound_enabled = st.checkbox("🔊 Ativar alerta sonoro", value=False)

search_query = st.text_input("🔍 Filtrar por moeda (ex: BTC, ETH):").upper().strip()
placeholder = st.empty()

def calc_transaction(coin, corretora_valorizada, corretora_desvalorizada, preco_menor, preco_maior):
    saldos = db.get(coin)
    vender = saldos[corretora_valorizada] * 0.1
    comprar = (vender * preco_maior) / preco_menor

    order_sell(coin, corretora_valorizada, vender)
    order_buy(coin, corretora_desvalorizada, comprar)
    return

def order_sell(coin, corretora, amount):
    saldos = db.get(coin)
    saldos[corretora] -= amount
    db.update(coin, saldos)

def order_buy(coin, corretora, amount):
    saldos = db.get(coin)
    saldos[corretora] += amount
    db.update(coin, saldos)

def update_table():
    gateio_cache, mexc_asks = data_fetcher.fetch_all_data()
    table = []
    triggered_alert = False

    for gate_sym, mexc_sym in data_fetcher.PAIRS:
        symbol = gate_sym.replace("_USDT", "")
        bid = gateio_cache.get(gate_sym, {}).get("highest_bid")
        ask = mexc_asks.get(mexc_sym)
        bid = float(bid) if bid else None
        ask = float(ask) if ask else None

        if bid is None or ask is None:
            table.append([symbol, "-", "-", "-", "-"])
            continue

        spread_pct = (bid - ask) / ask * 100
        in_trade = st.session_state.active_trades.get(symbol, False)

        if not in_trade and spread_pct > alert_threshold:
            calc_transaction(symbol, "gateio", "mexc", preco_menor=ask, preco_maior=bid)
            st.session_state.active_trades[symbol] = True
            triggered_alert = True

        elif in_trade and spread_pct <= 0:
            calc_transaction(symbol, "mexc", "gateio", preco_menor=bid, preco_maior=ask)
            st.session_state.active_trades[symbol] = False
            triggered_alert = True

        hist = st.session_state.spread_history.setdefault(symbol, [])
        hist.append(spread_pct)
        if len(hist) > 50:
            hist.pop(0)
        std_dev = np.std(hist)

        table.append([symbol, f"{bid:.6f}", f"{ask:.6f}", spread_pct, f"{std_dev:.4f}"])

    return table, triggered_alert

if "initial_balances" not in st.session_state:
    moedas = [gate_sym.replace("_USDT", "") for gate_sym, _ in data_fetcher.PAIRS]
    st.session_state.initial_balances = {}
    for coin in moedas:
        saldos = db.get(coin)
        st.session_state.initial_balances[coin] = saldos.copy()

# Renderização da UI
with placeholder.container():
    st.markdown("### 📊 Monitor de Spreads e Execução Automática")
    table, alert = update_table()

    if search_query:
        table = [r for r in table if search_query in r[0]]

    rows = ""
    for symbol, bid, ask, spread, std_dev in table:
        bg = ""
        val = f"{spread:.2f}%"
        if spread == "-":
            val = "-"
        else:
            if spread > alert_threshold:
                bg = "background-color: #c6efce;"
            elif spread < -alert_threshold:
                bg = "background-color: #f2c7c5;"
        rows += f"<tr><td>{symbol}</td><td>{bid}</td><td>{ask}</td><td style='{bg}'>{val}</td><td>{std_dev}</td></tr>"
    html = (
        "<table>"
        "<thead><tr><th>Moeda</th><th>Gate.io BID</th><th>MEXC ASK</th><th>Spread %</th><th>Desvio Padrão</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("### 💰 Saldos em cada Corretora por Moeda (com lucro/prejuízo e variação)")

    moedas = [gate_sym.replace("_USDT", "") for gate_sym, _ in data_fetcher.PAIRS]
    saldo_rows = ""

    gateio_cache, mexc_asks = data_fetcher.fetch_all_data()

    for coin in moedas:
        saldos = db.get(coin)
        gateio_saldo = saldos.get("gateio", 0)
        mexc_saldo = saldos.get("mexc", 0)

        init_saldos = st.session_state.initial_balances.get(coin, {"gateio": 0, "mexc": 0})
        init_gateio = init_saldos.get("gateio", 0)
        init_mexc = init_saldos.get("mexc", 0)

        gateio_var = ((gateio_saldo - init_gateio) / init_gateio * 100) if init_gateio != 0 else 0
        mexc_var = ((mexc_saldo - init_mexc) / init_mexc * 100) if init_mexc != 0 else 0

        sum_var_pct = gateio_var + mexc_var

        gate_sym = coin + "_USDT"
        mexc_sym = coin + "USDT"

        try:
            gateio_price = float(gateio_cache.get(gate_sym, {}).get("highest_bid") or 0)
        except:
            gateio_price = 0
        try:
            mexc_price = float(mexc_asks.get(mexc_sym) or 0)
        except:
            mexc_price = 0

        valor_gateio = gateio_saldo * gateio_price
        valor_mexc = mexc_saldo * mexc_price
        total_usd = valor_gateio + valor_mexc
        lucro_prejuizo = total_usd - 200

        lucro_style = "color: green;" if lucro_prejuizo >= 0 else "color: red;"
        if round(sum_var_pct, 2) > 0:
            profit_cell_style = "background-color: #c6efce; color: black;"
        elif round(sum_var_pct, 2) < 0:
            profit_cell_style = "background-color: #f2c7c5; color: black;"
        else:
            profit_cell_style = "color: black;"
                        
        saldo_rows += (
            f"<tr>"
            f"<td>{coin}</td>"
            f"<td>{gateio_saldo:.6f} ({gateio_var:+.2f}%)</td>"
            f"<td>{mexc_saldo:.6f} ({mexc_var:+.2f}%)</td>"
            f"<td>${total_usd:.2f}</td>"
            f"<td style='{profit_cell_style}'>{sum_var_pct:+.2f}%</td>"
            f"<td style='{lucro_style}'>${lucro_prejuizo:.2f}</td>"
            f"</tr>"
        )

    saldo_html = (
        "<table>"
        "<thead><tr>"
        "<th>Moeda</th><th>Gate.io Saldo</th><th>MEXC Saldo</th><th>Valor Total (USD)</th><th>Variação Somada (%)</th><th>Lucro / Prejuízo</th>"
        "</tr></thead>"
        f"<tbody>{saldo_rows}</tbody>"
        "</table>"
    )
    st.markdown(saldo_html, unsafe_allow_html=True)

    # Gráfico histórico
    keys = [k for k,v in st.session_state.spread_history.items() if v]
    if keys:
        st.markdown("### 📈 Histórico de Spread (%) por Moeda")
        sel = st.selectbox("Escolha uma moeda:", keys)
        st.line_chart(st.session_state.spread_history[sel])
    else:
        st.info("Aguardando dados para construir o gráfico…")

    if alert and sound_enabled:
        st.markdown("""
            <audio autoplay>
                <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
            </audio>
        """, unsafe_allow_html=True)

st.markdown("""
    <style>
        * { transition: none !important; opacity: 1 !important; }
        [data-testid="stAppViewContainer"] { opacity: 1 !important; }
        [data-baseweb="tab-panel"] { opacity: 1 !important; }
    </style>
""", unsafe_allow_html=True)

st_autorefresh(interval=refresh_rate * 1000, key="refresh")
