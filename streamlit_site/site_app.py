"""Professional Streamlit site for Realtime Quant Prototype (standalone).

This app is deployed from `streamlit_site/` and imports core logic from the
main repo without modifying main code. It focuses on presentation quality and
export features while keeping the analytics intact.
"""
from pathlib import Path
import sys

# add repo root to path so `src` and `tools` are importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from typing import List
import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.storage import ticks_to_ohlcv
from src.analytics import ols_hedge_ratio, construct_spread, rolling_zscore, adf_test, rolling_corr
from src.alerts import zscore_alerts
from tools.gen_synthetic_ticks import gen

st.set_page_config(page_title="Realtime Quant — Professional Site", layout="wide")

# --- CSS / styling ---
with open(Path(__file__).parent / "assets" / "style.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.header("Realtime Quantitative Analytics — Professional Demo")
st.markdown("Lightweight, reproducible research UI (selection-oriented, reproducible).")

# Sidebar controls
with st.sidebar:
    st.subheader("Data & Run")
    use_demo = st.radio("Data source", ["Demo synthetic", "Upload CSV"], index=0)
    if use_demo == "Demo synthetic":
        n = st.number_input("Ticks per symbol", min_value=120, max_value=100000, value=600, step=60)
        symbols = st.text_input("Symbols (space-separated)", value="SYM1 SYM2").strip().split()
        if st.button("Generate demo"):
            frames = [gen(s, n=n, seed=42 + i) for i, s in enumerate(symbols)]
            st.session_state["df"] = pd.concat(frames).sort_values("timestamp").reset_index(drop=True)
    else:
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded is not None:
            st.session_state["df"] = pd.read_csv(uploaded)

    st.markdown("---")
    st.subheader("Analytics")
    interval = st.selectbox("OHLCV interval", ["1s", "1m", "5m"], index=0)
    rolling_window = st.slider("Rolling window (periods)", 10, 500, 60, 10)
    z_threshold = st.slider("Z-score alert threshold", 1.0, 5.0, 2.0, 0.1)
    st.markdown("---")
    st.markdown("**Exports**")
    st.checkbox("Enable PNG export", value=True, key="enable_png")

# Helper
def ensure_data() -> pd.DataFrame:
    return st.session_state.get("df")

# Main layout: tabs
df = ensure_data()
if df is None:
    st.info("No data in session. Use the sidebar to generate demo data or upload a CSV.")
    st.stop()

# show dataset preview
st.subheader("Data sample")
st.dataframe(df.head())

# symbols
symbols = df["symbol"].unique().tolist()
if len(symbols) < 1:
    st.error("No symbols found in provided data")
    st.stop()

col1, col2 = st.columns([3, 1])
with col2:
    symbol_a = st.selectbox("Symbol A", options=symbols, index=0)
    symbol_b = st.selectbox("Symbol B", options=symbols, index=1 if len(symbols) > 1 else 0)
    if symbol_a == symbol_b:
        st.warning("Symbol A and B are the same — select two different symbols for pair analytics")

# compute OHLCV bars
ohlcv = ticks_to_ohlcv(df, interval=interval)

# Overview: combined price plot
st.subheader("Overview")
close_df = ohlcv["close"].unstack(level=0)

fig = go.Figure()
for sym in close_df.columns:
    fig.add_trace(go.Scatter(x=close_df.index, y=close_df[sym], mode="lines", name=sym))
fig.update_layout(title="Close Price — All Symbols", xaxis_title="Time", yaxis_title="Price")
st.plotly_chart(fig, use_container_width=True)

# Pair analytics
st.subheader("Pair Analytics")
try:
    a = close_df[symbol_a].dropna()
    b = close_df[symbol_b].dropna()
    pair = pd.concat([a, b], axis=1).dropna()
    a = pair.iloc[:, 0]
    b = pair.iloc[:, 1]

    beta = ols_hedge_ratio(a, b)
    st.markdown(f"**OLS hedge ratio (A ~ B):** `{beta:.6f}`")

    spread = construct_spread(a, b, beta)
    z = rolling_zscore(spread, window=rolling_window)
    corr = rolling_corr(a, b, window=rolling_window)

    # spread + zscore plot
    fig2 = make_subplots_rows = None
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=spread.index, y=spread.values, name="spread", yaxis="y1"))
    fig2.add_trace(go.Scatter(x=z.index, y=z.values, name="zscore", yaxis="y2"))
    fig2.update_layout(
        title=f"Spread and Rolling Z-score ({rolling_window})",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Spread", side="left"),
        yaxis2=dict(title="Z-score", overlaying="y", side="right"),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # rolling correlation
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=corr.index, y=corr.values, name="rolling_corr"))
    fig3.update_layout(title=f"Rolling Correlation ({rolling_window})", yaxis=dict(range=[-1, 1]))
    st.plotly_chart(fig3, use_container_width=True)

    # ADF
    adf_res = adf_test(spread)
    st.code(adf_res)

    # alerts
    alerts = zscore_alerts(z, threshold=z_threshold)
    st.markdown(f"**Alerts:** {len(alerts)} where |z| > {z_threshold}")
    if alerts:
        st.dataframe(pd.DataFrame(alerts))

    # export
    export_df = pd.concat([a.rename(symbol_a), b.rename(symbol_b), spread.rename("spread"), z.rename("zscore")], axis=1)
    csv = export_df.to_csv()
    st.download_button("Download pair CSV", csv, file_name="pair_analysis.csv", mime="text/csv")

    if st.session_state.get("enable_png"):
        # PNG snapshot of the spread chart
        img_bytes = fig2.to_image(format="png", width=1200, height=600)
        st.download_button("Download spread PNG", data=img_bytes, file_name="spread.png", mime="image/png")

except Exception as exc:  # pragma: no cover - UI-run only
    st.error(f"Error computing pair analytics: {exc}")

st.markdown("---")
st.caption("This site is a presentation layer. Replace the demo generator with a WebSocket source for live data ingestion while keeping the same analytics pipeline.")
