"""Generate simple synthetic tick CSV for demo and tests."""
import argparse
import numpy as np
import pandas as pd


def gen(symbol: str, n: int = 1000, seed: int = 42, start_price: float = 100.0):
    rng = np.random.default_rng(seed)
    # simple random walk
    steps = rng.normal(loc=0.0, scale=0.1, size=n)
    prices = start_price + np.cumsum(steps)
    quantities = rng.integers(1, 10, size=n)
    timestamps = pd.date_range("2025-01-01", periods=n, freq="s")
    return pd.DataFrame({"timestamp": timestamps, "symbol": symbol, "price": prices, "quantity": quantities})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", nargs="+", default=["SYM1", "SYM2"])
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--out", default="synthetic_ticks.csv")
    args = p.parse_args()

    frames = []
    for i, s in enumerate(args.symbols):
        frames.append(gen(s, n=args.n, seed=42 + i, start_price=100 + 10 * i))
    df = pd.concat(frames).sort_values("timestamp")
    df.to_csv(args.out, index=False)
    print(f"Written {args.out}")
