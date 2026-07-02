"""Comparative indicators derived from cumulative hazard."""

from __future__ import annotations

import pandas as pd

from src.analysis.hazard import h_at_age
from src.analysis.milestones import milestone_long, milestone_wide
from src.config.settings import K_MAX


DEFAULT_FIXED_AGES = (60, 70, 80, 90, 100)


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


def fixed_age_hazards(
    df: pd.DataFrame,
    *,
    ages: tuple[int, ...] = DEFAULT_FIXED_AGES,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Calculate H(age) for fixed ages such as 60, 70, 80, 90 and 100."""
    rows = []
    for keys, group in df.groupby(list(group_cols), dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["age_min"] = float(group["age"].min())
        row["age_max"] = float(group["age"].max())
        row["H_max"] = float(group["H"].max())
        for age in ages:
            row[f"H_{age}"] = h_at_age(group, age)
        rows.append(row)
    return pd.DataFrame(rows)


def build_indicators(
    df: pd.DataFrame,
    *,
    k_max: int = K_MAX,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Combine fixed-age hazards, l(100), and milestone ages in one wide table."""
    h100 = h100_by_group(df, group_cols=group_cols)
    fixed = fixed_age_hazards(df, group_cols=group_cols)
    milestones = milestone_wide(df, k_max=k_max, group_cols=group_cols)
    return (
        fixed.merge(h100, on=list(group_cols), how="left", suffixes=("", "_exact"))
        .drop(columns=["H_100_exact"], errors="ignore")
        .merge(milestones, on=list(group_cols), how="left")
    )


def build_milestone_long(
    df: pd.DataFrame,
    *,
    k_max: int = K_MAX,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Return milestone ages in long format for plotting."""
    return milestone_long(df, k_max=k_max, group_cols=group_cols)


def milestone_differences(
    milestones_long: pd.DataFrame,
    *,
    reference_country: str,
    group_col: str = "country",
) -> pd.DataFrame:
    """Compare each location's milestone ages against a reference location."""
    reference = milestones_long.loc[
        milestones_long[group_col] == reference_country, ["k", "age_at_k"]
    ].rename(columns={"age_at_k": "reference_age_at_k"})
    compared = milestones_long.merge(reference, on="k", how="inner")
    compared["difference_years"] = compared["age_at_k"] - compared["reference_age_at_k"]
    compared["reference_country"] = reference_country
    return compared.loc[compared[group_col] != reference_country].copy()
