"""Simple rule-based alerts."""
from typing import List
import pandas as pd


def zscore_alerts(z: pd.Series, threshold: float = 2.0) -> List[dict]:
    """Return alert dicts for times where |z| > threshold."""
    out = []
    if z is None or z.empty:
        return out
    mask = z.abs() > threshold
    for t, val in z[mask].items():
        out.append({"timestamp": t, "zscore": float(val)})
    return out
