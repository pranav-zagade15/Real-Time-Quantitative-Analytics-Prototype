import numpy as np
import pandas as pd
from src.analytics import ols_hedge_ratio, rolling_zscore, adf_test, construct_spread, rolling_corr


def test_ols_hedge_ratio():
    np.random.seed(0)
    x = np.arange(100).astype(float)
    y = 2.0 * x + np.random.normal(scale=0.01, size=x.shape)
    x_s = pd.Series(x)
    y_s = pd.Series(y)
    beta = ols_hedge_ratio(y_s, x_s)
    assert abs(beta - 2.0) < 0.01


def test_rolling_zscore():
    s = pd.Series(np.arange(100).astype(float))
    z = rolling_zscore(s, window=10)
    # last value should be 0 because it's linear increasing; non-zero but finite
    assert not z.isna().all()


def test_construct_spread_and_corr():
    # Make two correlated series
    rng = np.random.default_rng(1)
    x = pd.Series(np.linspace(0, 10, 200))
    y = 1.5 * x + rng.normal(scale=0.01, size=x.shape)
    beta = ols_hedge_ratio(y, x)
    spread = construct_spread(y, x, beta)
    # spread should be near zero mean
    assert abs(spread.mean()) < 0.1
    # rolling correlation near 1
    rc = rolling_corr(y, x, window=20)
    assert (rc.dropna() > 0.9).any()


def test_adf_on_stationary_series():
    # AR(1) stationary series
    rng = np.random.default_rng(0)
    x = [0.0]
    for _ in range(200):
        x.append(0.5 * x[-1] + rng.normal())
    s = pd.Series(x)
    res = adf_test(s)
    assert res["pvalue"] < 0.1
