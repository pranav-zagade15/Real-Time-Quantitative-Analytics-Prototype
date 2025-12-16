import pandas as pd
from src.alerts import zscore_alerts


def test_zscore_alerts():
    idx = pd.date_range("2025-01-01", periods=5, freq="S")
    z = pd.Series([0.0, 1.0, 2.5, -3.0, 0.5], index=idx)
    alerts = zscore_alerts(z, threshold=2.0)
    assert len(alerts) == 2
    assert any(a["zscore"] < 0 for a in alerts)