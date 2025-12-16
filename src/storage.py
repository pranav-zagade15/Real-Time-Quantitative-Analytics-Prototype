"""Storage and resampling utilities for tick data.

Functions are intentionally small and testable.
"""
from typing import Literal
import pandas as pd

Interval = Literal["1s", "1m", "5m"]


def ticks_to_ohlcv(ticks: pd.DataFrame, interval: Interval = "1s") -> pd.DataFrame:
    """Convert tick dataframe into OHLCV bars by symbol.

    Expects columns: ['timestamp', 'symbol', 'price', 'quantity'] where
    `timestamp` is either a pandas datetime or unix ms/ns integer.

    Returns a MultiIndex DataFrame (symbol, timestamp) with columns: open/high/low/close/volume
    """
    df = ticks.copy()
    if df.empty:
        return pd.DataFrame()

    # Robust parsing: accept ISO strings with fractional seconds and integers
    orig_ts = df["timestamp"].copy()
    try:
        df["timestamp"] = pd.to_datetime(orig_ts, infer_datetime_format=True, errors="coerce")
        if df["timestamp"].isna().any():
            # fallback: parse element-wise from original strings (handles mixed formats)
            df["timestamp"] = orig_ts.astype(str).apply(pd.to_datetime)
    except Exception:
        # Last-resort: let pandas infer per-element from original values
        df["timestamp"] = orig_ts.astype(str).apply(pd.to_datetime)
    df = df.set_index("timestamp")

    out_frames = []
    for sym, g in df.groupby("symbol"):
        g = g.sort_index()
        # price aggregation
        ohlc = g["price"].resample(interval).ohlc()
        vol = g["quantity"].resample(interval).sum().rename("volume")
        merged = pd.concat([ohlc, vol], axis=1)
        merged["symbol"] = sym
        out_frames.append(merged)

    res = pd.concat(out_frames)
    res = res.reset_index().set_index(["symbol", "timestamp"]).sort_index()
    return res
