"""Comparative indicators derived from cumulative hazard."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.hazard import h_at_age
from src.analysis.milestones import milestone_long, milestone_wide
from src.config.settings import K_MAX


DEFAULT_FIXED_AGES = (60, 70, 80, 90, 100)
CONVENTIONAL_INDICATORS = ("e0_approx", "e50_approx", "e90_approx", "modal_age", "median_age")
CORRELATION_INDICATORS = (
    "H_max",
    "H_60",
    "H_70",
    "H_80",
    "H_90",
    "x_H1",
    "e0_approx",
    "e50_approx",
    "modal_age",
    "median_age",
)


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


def median_age_at_death(group: pd.DataFrame) -> float:
    """Estimate the age where normalized survival l(x) crosses 0.5."""
    data = group.dropna(subset=["age", "l"]).sort_values("age")
    if data.empty or data["l"].min() > 0.5 or data["l"].max() < 0.5:
        return float("nan")

    ordered = data.sort_values("l")
    unique_l, unique_idx = np.unique(ordered["l"].to_numpy(float), return_index=True)
    unique_age = ordered["age"].to_numpy(float)[unique_idx]
    return float(np.interp(0.5, unique_l, unique_age))


def modal_age_at_death(group: pd.DataFrame, *, min_age: float = 10) -> float:
    """Estimate the adult modal age at death from declines in l(x)."""
    data = group.dropna(subset=["age", "l"]).sort_values("age")
    if len(data) < 3:
        return float("nan")

    age = data["age"].to_numpy(float)
    survival = data["l"].to_numpy(float)
    interval_width = np.diff(age)
    deaths = survival[:-1] - survival[1:]
    death_age = age[:-1] + interval_width / 2

    ok = np.isfinite(death_age) & np.isfinite(deaths) & (death_age > min_age)
    if not ok.any():
        return float("nan")
    return float(death_age[ok][np.argmax(deaths[ok])])


def remaining_life_expectancy_approx(group: pd.DataFrame, target_age: float) -> float:
    """Approximate remaining life expectancy at a target age from l(x).

    This integrates the observed survival curve using the trapezoid rule. It is
    a period-table approximation and does not extrapolate beyond the final age.
    """
    data = group.dropna(subset=["age", "l"]).sort_values("age")
    if len(data) < 2:
        return float("nan")

    age = data["age"].to_numpy(float)
    survival = data["l"].to_numpy(float)
    if target_age < age.min() or target_age >= age.max():
        return float("nan")

    l_target = np.interp(target_age, age, survival)
    if not np.isfinite(l_target) or l_target <= 0:
        return float("nan")

    future_age = age[age > target_age]
    future_survival = survival[age > target_age]
    integration_age = np.concatenate([[target_age], future_age])
    integration_survival = np.concatenate([[l_target], future_survival])
    person_years = np.trapezoid(integration_survival, integration_age)
    return float(person_years / l_target)


def conventional_indicators(
    df: pd.DataFrame,
    *,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Calculate conventional period-longevity indicators from l(x)."""
    rows = []
    for keys, group in df.groupby(list(group_cols), dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["e0_approx"] = remaining_life_expectancy_approx(group, 0)
        row["e50_approx"] = remaining_life_expectancy_approx(group, 50)
        row["e90_approx"] = remaining_life_expectancy_approx(group, 90)
        row["modal_age"] = modal_age_at_death(group)
        row["median_age"] = median_age_at_death(group)
        rows.append(row)
    return pd.DataFrame(rows)


def build_indicators(
    df: pd.DataFrame,
    *,
    k_max: int = K_MAX,
    group_cols: tuple[str, ...] = ("country", "year"),
) -> pd.DataFrame:
    """Combine hazard-based and conventional indicators in one wide table."""
    h100 = h100_by_group(df, group_cols=group_cols)
    fixed = fixed_age_hazards(df, group_cols=group_cols)
    conventional = conventional_indicators(df, group_cols=group_cols)
    milestones = milestone_wide(df, k_max=k_max, group_cols=group_cols)
    return (
        fixed.merge(h100, on=list(group_cols), how="left", suffixes=("", "_exact"))
        .drop(columns=["H_100_exact"], errors="ignore")
        .merge(conventional, on=list(group_cols), how="left")
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


def indicator_correlations(
    indicators: pd.DataFrame,
    *,
    columns: tuple[str, ...] = CORRELATION_INDICATORS,
    method: str = "spearman",
) -> pd.DataFrame:
    """Compute pairwise correlations among available indicators."""
    available = [col for col in columns if col in indicators.columns]
    return indicators[available].corr(method=method, min_periods=3)


def indicator_rankings(
    indicators: pd.DataFrame,
    *,
    columns: tuple[str, ...] = ("H_max", "H_90", "x_H1", "e0_approx", "median_age"),
) -> pd.DataFrame:
    """Rank locations across selected indicators.

    Lower H values are better, while higher ages and life expectancy values are
    better.
    """
    ranking = indicators[["country", "year", *[c for c in columns if c in indicators.columns]]].copy()
    lower_is_better = {"H_max", "H_60", "H_70", "H_80", "H_90", "H_100"}
    for column in columns:
        if column not in ranking.columns:
            continue
        ascending = column in lower_is_better
        ranking[f"rank_{column}"] = ranking[column].rank(ascending=ascending, method="average")
    return ranking
