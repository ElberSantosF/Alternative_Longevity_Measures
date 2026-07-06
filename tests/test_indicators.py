import math

import pandas as pd

from src.analysis.hazard import add_survival_hazard
from src.analysis.indicators import (
    build_indicators,
    age_band_hazard_contributions,
    conditional_survival_probabilities,
    indicator_correlations,
    indicator_rankings,
    median_age_at_death,
    modal_age_at_death,
    remaining_life_expectancy_approx,
    sex_indicator_gaps,
)


def _life_table():
    return add_survival_hazard(
        pd.DataFrame(
            {
                "country": ["A"] * 5,
                "year": [2025] * 5,
                "age": [0, 10, 20, 30, 40],
                "lx": [100000, 80000, 50000, 20000, 0.01],
            }
        )
    )


def test_median_age_at_death_interpolates_l_equals_half():
    assert math.isclose(median_age_at_death(_life_table()), 20.0)


def test_modal_age_at_death_uses_largest_adult_survival_drop():
    assert math.isclose(modal_age_at_death(_life_table()), 15.0)


def test_remaining_life_expectancy_approx_uses_area_under_survival():
    assert math.isclose(remaining_life_expectancy_approx(_life_table(), 0), 20.0000005)


def test_build_indicators_adds_conventional_columns():
    out = build_indicators(_life_table())

    assert {"e0_approx", "e50_approx", "modal_age", "median_age"}.issubset(out.columns)


def test_conditional_survival_probabilities_divide_l_values():
    out = conditional_survival_probabilities(_life_table(), transitions=((10, 30),))

    assert math.isclose(out["conditional_survival"].iloc[0], 0.25)


def test_age_band_hazard_contributions_use_hazard_increments():
    out = age_band_hazard_contributions(_life_table(), bands=((0, 20), (20, 40)))

    assert math.isclose(out.loc[out["age_band"] == "0-20", "hazard_increment"].iloc[0], -math.log(0.5))
    assert math.isclose(out["share_of_observed_increment"].sum(), 1.0)


def test_sex_indicator_gaps_compare_female_and_male_rows():
    indicators = pd.DataFrame(
        {
            "country": ["North Brazil - Female", "North Brazil - Male"],
            "year": [2025, 2025],
            "H_90": [1.2, 1.5],
            "median_age": [86.0, 82.0],
        }
    )

    out = sex_indicator_gaps(indicators, columns=("H_90", "median_age"))

    assert math.isclose(
        out.loc[out["indicator"] == "median_age", "gap_female_minus_male"].iloc[0],
        4.0,
    )


def test_correlation_and_ranking_helpers_return_tables():
    indicators = pd.DataFrame(
        {
            "country": ["A", "B", "C"],
            "year": [2025, 2025, 2025],
            "H_max": [1.0, 2.0, 3.0],
            "H_90": [0.8, 1.2, 1.6],
            "x_H1": [90.0, 85.0, 80.0],
            "e0_approx": [80.0, 75.0, 70.0],
            "median_age": [82.0, 78.0, 74.0],
        }
    )

    correlations = indicator_correlations(indicators)
    rankings = indicator_rankings(indicators)

    assert "H_max" in correlations.columns
    assert "rank_H_max" in rankings.columns
    assert rankings.loc[rankings["country"] == "A", "rank_H_max"].iloc[0] == 1.0
