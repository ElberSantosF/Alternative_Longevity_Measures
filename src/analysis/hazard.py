"""Cumulative hazard calculations for life tables."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config.settings import EPSILON


def add_survival_hazard(
    df: pd.DataFrame,
    *,
    group_cols: tuple[str, ...] = ("country", "year"),
    age_col: str = "age",
    lx_col: str = "lx",
    epsilon: float = EPSILON,
) -> pd.DataFrame:
    """Add normalized survival ``l`` and cumulative hazard ``H``.

    ``l`` is calculated as ``lx / l0``, where ``l0`` is the ``lx`` value at the
    minimum observed age inside each group. ``H`` is ``-log(l)``.
    """
    required = set(group_cols) | {age_col, lx_col}
    missing = required.difference(df.columns)
    if missing:
        raise KeyError(f"Missing required columns: {sorted(missing)}")

    out = df.copy()
    out[age_col] = pd.to_numeric(out[age_col], errors="coerce")
    out[lx_col] = pd.to_numeric(out[lx_col], errors="coerce")
    out = out.dropna(subset=[age_col, lx_col]).sort_values(list(group_cols) + [age_col])
    l0 = out.groupby(list(group_cols), dropna=False)[lx_col].transform("first")
    if ((~np.isfinite(l0)) | (l0 <= 0)).any():
        raise ValueError("Each group must have a positive lx at the minimum age.")

    out["l0"] = l0
    out["l"] = np.maximum(out[lx_col] / out["l0"], epsilon)
    out["H"] = -np.log(out["l"])
    return out


def h_at_age(
    df: pd.DataFrame,
    age: float,
    *,
    age_col: str = "age",
    hazard_col: str = "H",
) -> float:
    """Return H at an exact age, or NaN when the age is absent."""
    values = df.loc[df[age_col] == age, hazard_col]
    if values.empty:
        return float("nan")
    return float(values.iloc[0])
