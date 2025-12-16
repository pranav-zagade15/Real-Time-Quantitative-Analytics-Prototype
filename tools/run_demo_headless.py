"""Headless demo: generate synthetic ticks and run analytics pipeline, printing outputs.

Usage: python tools/run_demo_headless.py --n 240
"""
import argparse
import sys
from pathlib import Path

# ensure repo root is on path so `tools` and `src` are importable when run as a script
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.gen_synthetic_ticks import gen
import pandas as pd
from src.storage import ticks_to_ohlcv
from src.analytics import ols_hedge_ratio, construct_spread, rolling_zscore, adf_test
from src.alerts import zscore_alerts


def main(symbols=("SYM1", "SYM2"), n=240, rolling_window=60, z_threshold=2.0):
    frames = [gen(s, n=n, seed=42 + i) for i, s in enumerate(symbols)]
    df = pd.concat(frames).sort_values("timestamp").reset_index(drop=True)

    print("--- HEADLESS DEMO REPORT ---")
    print(f"Generated ticks: {len(df)} rows; symbols: {symbols}")
    print(df.head().to_string(index=False))

    ohlcv = ticks_to_ohlcv(df, interval="1s")
    print("\nOHLCV sample (per symbol, first 4 rows):")
    print(ohlcv.groupby(level=0).head(4).reset_index().to_string(index=False))

    # pick two symbols
    a_sym, b_sym = symbols[0], symbols[1]
    try:
        a_close = ohlcv.loc[(a_sym,), "close"].droplevel(0).dropna()
        b_close = ohlcv.loc[(b_sym,), "close"].droplevel(0).dropna()
    except Exception as e:
        # fallback: unstack
        close_df = ohlcv["close"].unstack(level=0)
        a_close = close_df[a_sym].dropna()
        b_close = close_df[b_sym].dropna()

    pair = pd.concat([a_close, b_close], axis=1).dropna()
    a = pair.iloc[:, 0]
    b = pair.iloc[:, 1]

    beta = ols_hedge_ratio(a, b)
    print(f"\nOLS hedge ratio (A ~ B): {beta:.6f}")

    spread = construct_spread(a, b, beta)
    z = rolling_zscore(spread, window=rolling_window)
    print("\nSpread sample:")
    print(spread.tail(8).to_string())
    print("\nZ-score sample:")
    print(z.tail(8).to_string())

    adf_res = adf_test(spread)
    print(f"\nADF test: statistic={adf_res['statistic']}, pvalue={adf_res['pvalue']}")

    alerts = zscore_alerts(z, threshold=z_threshold)
    print(f"\nAlerts (|z|>{z_threshold}): {len(alerts)}")
    if alerts:
        print(pd.DataFrame(alerts).to_string(index=False))

    # Save pair csv
    out = pd.concat([a.rename(f"{a_sym}"), b.rename(f"{b_sym}"), spread.rename("spread"), z.rename("zscore")], axis=1)
    out.to_csv("pair_analysis.csv")
    print("\nWrote pair_analysis.csv")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=240)
    p.add_argument("--symbols", nargs="+", default=["SYM1", "SYM2"]) 
    p.add_argument("--window", type=int, default=60)
    p.add_argument("--threshold", type=float, default=2.0)
    args = p.parse_args()
    main(symbols=args.symbols, n=args.n, rolling_window=args.window, z_threshold=args.threshold)
