import math

import numpy as np
import pandas as pd

from src.analysis.hazard import add_survival_hazard
from src.analysis.milestones import x_at_Hk


def test_add_survival_hazard_uses_lx_at_minimum_age_as_l0():
    df = pd.DataFrame(
        {
            "country": ["TST", "TST", "TST"],
            "year": [2025, 2025, 2025],
            "age": [0, 1, 2],
            "lx": [100000, 90000, 50000],
        }
    )

    out = add_survival_hazard(df)

    assert np.allclose(out["l"], [1.0, 0.9, 0.5])
    assert math.isclose(out.loc[out["age"] == 2, "H"].iloc[0], -math.log(0.5))


def test_add_survival_hazard_excludes_ages_above_90_by_default():
    df = pd.DataFrame(
        {
            "country": ["TST", "TST", "TST"],
            "year": [2025, 2025, 2025],
            "age": [89, 90, 91],
            "lx": [100000, 90000, 80000],
        }
    )

    out = add_survival_hazard(df)

    assert out["age"].tolist() == [89, 90]


def test_x_at_Hk_interpolates_linearly():
    age = [0, 10, 20]
    hazard = [0, 1, 3]

    assert math.isclose(x_at_Hk(age, hazard, 2), 15.0)


def test_x_at_Hk_returns_nan_outside_range():
    assert math.isnan(x_at_Hk([0, 10], [0.0, 0.5], 1.0))
