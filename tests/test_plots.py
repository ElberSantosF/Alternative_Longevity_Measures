"""Contract tests for the report and presentation plotting system."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from matplotlib.figure import Figure
import pandas as pd
import pytest

from src.analysis.hazard import add_survival_hazard
from src.data.loaders import load_life_tables_from_metadata
from src.visualization.plots import (
    plot_benchmark_hazard_gap_vs_chile,
    plot_regional_hazard_by_sex,
    plot_sex_hazard_gap_by_region,
)
from src.visualization.style import (
    PROFILES,
    REGION_COLORS,
    REGION_ORDER,
    display_label,
)


EXPECTED_REGION_COLORS = {
    "North Brazil": "#0072B2",
    "Northeast Brazil": "#E69F00",
    "Central-West Brazil": "#D55E00",
    "Southeast Brazil": "#009E73",
    "South Brazil": "#CC79A7",
    "Chile": "#3D4652",
}

EXPECTED_LABELS_PT = {
    "North Brazil": "Norte",
    "Northeast Brazil": "Nordeste",
    "Central-West Brazil": "Centro-Oeste",
    "Southeast Brazil": "Sudeste",
    "South Brazil": "Sul",
    "Chile": "Chile",
    "Female": "Mulheres",
    "Male": "Homens",
}


@pytest.fixture(scope="module")
def life_tables():
    """Use the same local spreadsheets and hazard calculation as the notebook."""

    return add_survival_hazard(load_life_tables_from_metadata())


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.mark.parametrize(
    ("profile", "expected_size"),
    [
        ("report", (7.2, 4.2)),
        ("slides", (12.0, 6.75)),
    ],
)
def test_plot_returns_figure_saves_file_and_uses_profile_dimensions(
    life_tables, tmp_path, profile, expected_size
):
    output_path = tmp_path / f"sex_gap_{profile}.png"

    fig = plot_sex_hazard_gap_by_region(
        life_tables,
        output_path=output_path,
        profile=profile,
    )

    assert isinstance(fig, Figure)
    assert tuple(fig.get_size_inches()) == pytest.approx(expected_size)
    assert fig._figure_profile is PROFILES[profile]
    assert output_path.is_file()
    assert output_path.stat().st_size > 0


def test_region_palette_and_reader_facing_labels_are_stable():
    assert REGION_COLORS == EXPECTED_REGION_COLORS
    assert len(set(REGION_COLORS.values())) == len(REGION_COLORS)
    assert {key: display_label(key) for key in EXPECTED_LABELS_PT} == EXPECTED_LABELS_PT
    assert display_label("North Brazil - Female") == "Norte \u2014 Mulheres"


def test_curve_plot_rejects_multiple_years_instead_of_aggregating(life_tables):
    first_country = life_tables["country"].iloc[0]
    another_year = life_tables.loc[life_tables["country"] == first_country].copy()
    another_year["year"] = another_year["year"].astype(int) + 1
    multiple_years = pd.concat([life_tables, another_year], ignore_index=True)

    with pytest.raises(ValueError, match="ano"):
        plot_regional_hazard_by_sex(multiple_years, profile="report")


def test_benchmark_has_one_panel_per_sex_and_stable_region_colors(life_tables):
    fig = plot_benchmark_hazard_gap_vs_chile(life_tables, profile="report")

    assert isinstance(fig, Figure)
    assert len(fig.axes) == 2
    assert [ax.get_title() for ax in fig.axes] == ["Mulheres", "Homens"]
    assert fig.axes[0].get_shared_y_axes().joined(fig.axes[0], fig.axes[1])

    expected_colors = [REGION_COLORS[region].lower() for region in REGION_ORDER]
    for ax in fig.axes:
        region_lines = [line for line in ax.lines if len(line.get_xdata()) > 2]
        assert len(region_lines) == len(REGION_ORDER)
        assert [to_hex(line.get_color()) for line in region_lines] == expected_colors
