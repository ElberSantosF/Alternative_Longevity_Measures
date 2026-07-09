"""Generate report figures from the registered life tables."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.hazard import add_survival_hazard
from src.analysis.indicators import (
    age_band_hazard_contributions,
    build_indicators,
    build_milestone_long,
    conditional_survival_probabilities,
    sex_indicator_gaps,
)
from src.config.settings import FIGURES_DIR, K_MAX
from src.data.loaders import load_life_tables_from_metadata
from src.visualization.plots import (
    plot_age_band_hazard_contributions,
    plot_benchmark_hazard_gap_vs_chile,
    plot_conditional_survival,
    plot_hazard_curves,
    plot_indicator_bars_brazil_regions,
    plot_regional_hazard_by_sex,
    plot_regional_survival_by_sex,
    plot_sex_hazard_gap_by_region,
    plot_sex_indicator_gaps,
    plot_survival_curves,
)


def main() -> None:
    raw = load_life_tables_from_metadata()
    life_tables = add_survival_hazard(raw)
    indicators = build_indicators(life_tables, k_max=K_MAX)
    build_milestone_long(life_tables, k_max=K_MAX)

    conditional_survival = conditional_survival_probabilities(life_tables)
    age_band_contributions = age_band_hazard_contributions(life_tables)
    sex_gaps = sex_indicator_gaps(indicators)
    male_life_tables = life_tables[life_tables["country"].str.contains("Male")].copy()
    male_20_60_survival = conditional_survival_probabilities(
        male_life_tables,
        transitions=((20, 40), (40, 60), (20, 60)),
    )
    male_20_60_hazard = age_band_hazard_contributions(
        male_life_tables,
        bands=((20, 40), (40, 60), (20, 60)),
    )

    figure_calls = [
        (plot_hazard_curves, life_tables, "hazard_curves_all.png"),
        (plot_survival_curves, life_tables, "survival_curves_all.png"),
        (plot_regional_hazard_by_sex, life_tables, "brazil_regions_hazard_by_sex.png"),
        (plot_regional_survival_by_sex, life_tables, "brazil_regions_survival_by_sex.png"),
        (plot_indicator_bars_brazil_regions, indicators, "brazil_regions_indicator_bars.png"),
        (plot_sex_hazard_gap_by_region, life_tables, "sex_hazard_gap_by_region.png"),
        (plot_benchmark_hazard_gap_vs_chile, life_tables, "brazil_regions_vs_chile_hazard_gap.png"),
        (plot_conditional_survival, conditional_survival, "conditional_survival.png"),
        (plot_age_band_hazard_contributions, age_band_contributions, "age_band_hazard_contributions.png"),
        (plot_sex_indicator_gaps, sex_gaps, "sex_indicator_gaps.png"),
        (plot_conditional_survival, male_20_60_survival, "male_20_60_conditional_survival.png"),
        (plot_age_band_hazard_contributions, male_20_60_hazard, "male_20_60_hazard_contributions.png"),
    ]

    for plot_func, data, filename in figure_calls:
        plot_func(data, output_path=FIGURES_DIR / filename)
        plt.close("all")


if __name__ == "__main__":
    main()
