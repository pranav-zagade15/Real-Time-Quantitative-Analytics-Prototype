"""Quantitative analytics functions for relative-value research."""
"""Quantitative analytics functions for relative-value research.

All functions operate on Pandas Series and return Series or scalars where
appropriate. They are intentionally small and easily testable.
"""
from typing import Dict
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller


def ols_hedge_ratio(y: pd.Series, x: pd.Series) -> float:
    """Estimate hedge ratio from OLS: y = alpha + beta * x + eps -> return beta.

    Missing values are dropped pairwise. Returns the slope (beta) as float.
    """
    xy = pd.concat([y, x], axis=1).dropna()
    if xy.empty:
        raise ValueError("Insufficient data to estimate hedge ratio")
    y_clean = xy.iloc[:, 0]
    x_clean = xy.iloc[:, 1]
    x_const = sm.add_constant(x_clean)
    model = sm.OLS(y_clean, x_const).fit()
    return float(model.params[1])


def construct_spread(y: pd.Series, x: pd.Series, hedge_ratio: float) -> pd.Series:
    """Construct spread series: s = y - hedge_ratio * x"""
    return y - hedge_ratio * x


def rolling_zscore(s: pd.Series, window: int = 60) -> pd.Series:
    """Compute rolling z-score: (s - mean) / std using a rolling window.

    Uses population std (ddof=0) to be consistent and avoid small-sample
    instability in short windows.
    """
    mu = s.rolling(window, min_periods=1).mean()
    sd = s.rolling(window, min_periods=1).std(ddof=0)
    return (s - mu) / sd


def adf_test(s: pd.Series, **kwargs) -> Dict[str, float]:
    """Run Augmented Dickey-Fuller test and return a small summary dict."""
    arr = s.dropna().astype(float)
    if arr.size < 10:
        return {"statistic": float("nan"), "pvalue": 1.0, "usedlag": 0, "nobs": int(arr.size)}
    res = adfuller(arr, **kwargs)
    return {"statistic": float(res[0]), "pvalue": float(res[1]), "usedlag": int(res[2]), "nobs": int(res[3])}


def rolling_corr(a: pd.Series, b: pd.Series, window: int = 60) -> pd.Series:
    """Rolling Pearson correlation between two series using a fixed window."""
    return a.rolling(window).corr(b)
