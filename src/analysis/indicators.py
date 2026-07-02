"""Comparative indicators derived from cumulative hazard."""

from __future__ import annotations

import pandas as pd

from src.analysis.hazard import h_at_age
from src.analysis.milestones import milestone_long, milestone_wide
from src.config.settings import K_MAX


def h100_by_group(
    df: pd.DataFrame,
    *,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Calculate cumulative hazard at age 100 for each group."""
    rows = []
    for keys, group in df.groupby(list(group_cols), dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["H_100"] = h_at_age(group, 100)
        l_values = group.loc[group["age"] == 100, "l"]
        row["l_100"] = float(l_values.iloc[0]) if not l_values.empty else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def build_indicators(
    df: pd.DataFrame,
    *,
    k_max: int = K_MAX,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Combine H(100), l(100), and milestone ages in one wide table."""
    h100 = h100_by_group(df, group_cols=group_cols)
    milestones = milestone_wide(df, k_max=k_max, group_cols=group_cols)
    return h100.merge(milestones, on=list(group_cols), how="left")


def build_milestone_long(
    df: pd.DataFrame,
    *,
    k_max: int = K_MAX,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Return milestone ages in long format for plotting."""
    return milestone_long(df, k_max=k_max, group_cols=group_cols)

