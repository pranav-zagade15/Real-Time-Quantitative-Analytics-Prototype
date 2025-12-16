"""Streamlit research dashboard for realtime-quant prototype.

Features:
- Load demo or uploaded tick CSV
- Select timeframe (1s/1m/5m), rolling windows and pair of symbols
- Compute OLS hedge ratio, spread, rolling z-score, rolling correlation
- On-demand ADF test, rule-based alerts, CSV export
"""
from io import StringIO
import streamlit as st
import pandas as pd

from src.storage import ticks_to_ohlcv
from src.analytics import ols_hedge_ratio, construct_spread, rolling_zscore, adf_test, rolling_corr
from src.alerts import zscore_alerts
from tools.gen_synthetic_ticks import gen


st.set_page_config(page_title="Realtime Quant Prototype", layout="wide")
st.title("Realtime Quant Prototype — Research Dashboard")


with st.sidebar:
    st.header("Data")
    use_demo = st.checkbox("Use demo synthetic data", value=True)
    if use_demo:
        n = st.number_input("Ticks per symbol (demo)", min_value=120, max_value=100000, value=120)
        symbols = st.text_input("Symbols (space-separated)", value="SYM1 SYM2").split()
        if st.button("Generate demo data"):
            frames = [gen(s, n=n, seed=42 + i) for i, s in enumerate(symbols)]
            df = pd.concat(frames).sort_values("timestamp").reset_index(drop=True)
            st.session_state["df"] = df
    else:
        uploaded = st.file_uploader("Upload synthetic ticks CSV", type=["csv"]) 
        if uploaded is not None:
            df = pd.read_csv(uploaded)
            st.session_state["df"] = df

    st.header("Analysis")
    interval = st.selectbox("OHLCV interval", options=["1s", "1m", "5m"], index=0)
    rolling_window = st.number_input("Rolling window (periods)", min_value=10, max_value=1000, value=60)
    z_threshold = st.number_input("Z-score alert threshold", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
    st.write("--")
    st.write("Pair analytics")
    symbol_a = st.selectbox("Symbol A", options=["(none)"], index=0, key="sym_a")
    symbol_b = st.selectbox("Symbol B", options=["(none)"], index=0, key="sym_b")


def _ensure_data():
    return st.session_state.get("df") if "df" in st.session_state else None


df = _ensure_data()
if df is None:
    st.info("No data loaded. Use demo data or upload a synthetic ticks CSV (see tools/gen_synthetic_ticks.py).")
else:
    st.write("Data sample")
    st.dataframe(df.head())

    # populate symbol selections dynamically after data is loaded
    syms = df["symbol"].unique().tolist()
    symbol_a = st.sidebar.selectbox("Symbol A", options=syms, index=0, key="sym_a2")
    symbol_b = st.sidebar.selectbox("Symbol B", options=syms, index=1 if len(syms) > 1 else 0, key="sym_b2")

    # aggregate for both symbols
    bars = ticks_to_ohlcv(df, interval=interval)

    st.subheader("Price (close) — All symbols")
    # show combined close series per symbol as separate lines
    close_df = bars["close"].unstack(level=0)
    st.line_chart(close_df.ffill())

    st.subheader("Pair analytics")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Symbol A:** {symbol_a}")
        st.markdown(f"**Symbol B:** {symbol_b}")
        if st.button("Compute pair analytics"):
            try:
                a_close = close_df[symbol_a].dropna()
                b_close = close_df[symbol_b].dropna()
                # align series
                pair = pd.concat([a_close, b_close], axis=1).dropna()
                a = pair.iloc[:, 0]
                b = pair.iloc[:, 1]
                beta = ols_hedge_ratio(a, b)
                st.write(f"OLS hedge ratio (A ~ B): {beta:.6f}")
                spread = construct_spread(a, b, hedge_ratio=beta)
                z = rolling_zscore(spread, window=rolling_window)
                corr = rolling_corr(a, b, window=rolling_window)

                st.line_chart(pd.DataFrame({"spread": spread, "zscore": z}).fillna(method="ffill"))
                st.line_chart(corr)

                # ADF test on spread
                adf_res = adf_test(spread)
                st.write("ADF test:", adf_res)

                # alerts
                alerts = zscore_alerts(z, threshold=z_threshold)
                if alerts:
                    st.warning(f"{len(alerts)} alerts: show in table below")
                    st.table(pd.DataFrame(alerts))
                else:
                    st.write("No z-score alerts")

                # CSV export
                out = pd.concat([a, b, spread.rename("spread"), z.rename("zscore")], axis=1)
                csv = out.to_csv(index=True)
                st.download_button("Download pair CSV", data=csv, file_name="pair_analysis.csv", mime="text/csv")

            except Exception as exc:
                st.error(f"Error computing analytics: {exc}")
    with col2:
        st.markdown("**On-demand tests & notes**")
        if st.button("Run ADF on selected spread"):
            try:
                a_close = close_df[symbol_a].dropna()
                b_close = close_df[symbol_b].dropna()
                pair = pd.concat([a_close, b_close], axis=1).dropna()
                spread = construct_spread(pair.iloc[:, 0], pair.iloc[:, 1], ols_hedge_ratio(pair.iloc[:, 0], pair.iloc[:, 1]))
                st.json(adf_test(spread))
            except Exception as exc:
                st.error(f"ADF error: {exc}")

    st.caption("UI is research-oriented and intentionally minimal. For live connectivity, replace the demo generator with a Binance WebSocket source and feed ticks into the same in-memory buffer.")
