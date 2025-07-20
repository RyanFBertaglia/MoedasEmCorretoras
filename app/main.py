import streamlit as st
import time
import data_fetcher

data_fetcher.start_background_fetch()

st.set_page_config(page_title="Arbitragem Multi-Moeda REST", layout="wide")
st.title("🔁 Arbitragem Multi-Moeda (Gate.io BID / MEXC ASK)")

PAIRS = data_fetcher.PAIRS
placeholder = st.empty()

while True:
    with placeholder.container():
        st.markdown("### 📊 Monitor de Spreads")
        rows = []
        for gate_sym, mexc_sym in PAIRS:
            bid, ask = data_fetcher.get_pair_data(gate_sym, mexc_sym)
            if bid is None or ask is None or ask == 0:
                rows.append([gate_sym.replace("_usdt", "").upper(), "-", "-", "-"])
            else:
                pct = (bid - ask) / ask * 100
                color = "green" if pct > 0.5 else "black"
                rows.append([
                    gate_sym.replace("_usdt", "").upper(),
                    f"{bid:.6f}",
                    f"{ask:.6f}",
                    f"<span style='color:{color}'>{pct:.2f}%</span>"
                ])

        st.markdown(
            "<style>"
            "table { font-size: 16px; border-collapse: collapse; width: 100%; }"
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }"
            "th { background-color: #f2f2f2; }"
            "</style>", unsafe_allow_html=True
        )
        st.markdown(
            "<table><thead><tr><th>Moeda</th><th>Gate.io BID</th><th>MEXC ASK</th><th>Spread %</th></tr></thead><tbody>"
            + "".join(f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>" for r in rows)
            + "</tbody></table>",
            unsafe_allow_html=True
        )

    time.sleep(0.5)
