import pandas as pd
from src.storage import ticks_to_ohlcv


def test_ticks_to_ohlcv_simple():
    df = pd.DataFrame({
        "timestamp": ["2025-01-01T00:00:00", "2025-01-01T00:00:00.500000", "2025-01-01T00:00:01"],
        "symbol": ["SYM", "SYM", "SYM"],
        "price": [100.0, 101.0, 102.0],
        "quantity": [1, 2, 1],
    })
    o = ticks_to_ohlcv(df, interval="1s")
    # expect two rows (00:00:00 and 00:00:01)
    assert ("SYM", pd.Timestamp("2025-01-01T00:00:00")) in o.index
    assert ("SYM", pd.Timestamp("2025-01-01T00:00:01")) in o.index
    first = o.loc[("SYM", pd.Timestamp("2025-01-01T00:00:00"))]
    assert first["open"] == 100.0
    assert first["high"] == 101.0
    assert first["close"] == 101.0
    assert first["volume"] == 3
