"""Milestone ages for cumulative hazard levels."""

from __future__ import annotations

import numpy as np
import pandas as pd


def x_at_Hk(age, H, k: float) -> float:
    """Return the interpolated age where cumulative hazard reaches ``k``.

    This mirrors R's ``approx(x = H, y = age, xout = k)`` for monotonic life
    table hazards, returning ``NaN`` when ``k`` is outside the observed range.
    """
    age_arr = np.asarray(age, dtype=float)
    h_arr = np.asarray(H, dtype=float)
    ok = np.isfinite(age_arr) & np.isfinite(h_arr)
    if ok.sum() < 2:
        return float("nan")

    age_ok = age_arr[ok]
    h_ok = h_arr[ok]
    order = np.argsort(h_ok)
    h_sorted = h_ok[order]
    age_sorted = age_ok[order]

    unique_h, unique_idx = np.unique(h_sorted, return_index=True)
    unique_age = age_sorted[unique_idx]
    if k < unique_h.min() or k > unique_h.max():
        return float("nan")
    return float(np.interp(k, unique_h, unique_age))


def milestone_wide(
    df: pd.DataFrame,
    *,
    k_max: int,
    group_cols: tuple[str, ...] = ("country", "year"),
    age_col: str = "age",
    hazard_col: str = "H",
) -> pd.DataFrame:
    """Compute wide milestone columns ``x_H1`` ... ``x_H{k_max}`` by group."""
    rows = []
    for keys, group in df.groupby(list(group_cols), dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        for k in range(1, k_max + 1):
            row[f"x_H{k}"] = x_at_Hk(group[age_col], group[hazard_col], k)
        rows.append(row)
    return pd.DataFrame(rows)


def milestone_long(
    df: pd.DataFrame,
    *,
    k_max: int,
    group_cols: tuple[str, ...] = ("country", "year"),
    age_col: str = "age",
    hazard_col: str = "H",
) -> pd.DataFrame:
    """Compute milestone ages in long format with columns ``k`` and ``age_at_k``."""
    wide = milestone_wide(
        df,
        k_max=k_max,
        group_cols=group_cols,
        age_col=age_col,
        hazard_col=hazard_col,
    )
    value_cols = [f"x_H{k}" for k in range(1, k_max + 1)]
    long = wide.melt(
        id_vars=list(group_cols),
        value_vars=value_cols,
        var_name="milestone",
        value_name="age_at_k",
    )
    long["k"] = long["milestone"].str.replace("x_H", "", regex=False).astype(int)
    long["outlived_pct"] = (1 - np.exp(-long["k"])) * 100
    return long.dropna(subset=["age_at_k"])

