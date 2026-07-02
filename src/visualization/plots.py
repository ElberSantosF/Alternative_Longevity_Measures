"""Matplotlib/Seaborn plots matching the original R analyses."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from src.config.settings import FIGURES_DIR, VIRIDIS_CMAP


def _finish(fig, output_path: str | Path | None = None):
    fig.tight_layout()
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches="tight")
    return fig


def set_theme() -> None:
    """Apply a minimal plotting theme."""
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 120,
        }
    )


def plot_h100_over_time(series, output_path: str | Path | None = None):
    """Plot H(100) over birth cohorts/years by country."""
    set_theme()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.lineplot(data=series, x="year", y="H_100", hue="country", palette=VIRIDIS_CMAP, ax=ax)
    ax.set(
        xlabel="Year (cohort life table)",
        ylabel="H(100)",
        title="Expected death challenges to overcome to reach age 100",
    )
    ax.legend(title="Country", loc="best")
    return _finish(fig, output_path or FIGURES_DIR / "01_h100_over_time.png")


def plot_xh1_over_time(series, output_path: str | Path | None = None):
    """Plot the age where H reaches 1 over time."""
    set_theme()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.lineplot(data=series, x="year", y="x_H1", hue="country", palette=VIRIDIS_CMAP, ax=ax)
    ax.set(
        xlabel="Year (period life table)",
        ylabel="x[H=1]",
        title="Age at which individuals accumulate one lifetime challenge",
    )
    ax.legend(title="Country", loc="best")
    return _finish(fig, output_path or FIGURES_DIR / "02_xh1_over_time.png")


def plot_challenge_curves(milestones_long, output_path: str | Path | None = None):
    """Facet milestone curves x_Hk by country."""
    set_theme()
    grid = sns.relplot(
        data=milestones_long,
        x="year",
        y="age_at_k",
        hue="k",
        col="country",
        kind="line",
        palette=VIRIDIS_CMAP,
        height=4,
        aspect=0.95,
        facet_kws={"sharex": False, "sharey": True},
    )
    grid.set_axis_labels("Birth cohort", "Age where H reaches k")
    grid.set_titles("{col_name}")
    grid.fig.suptitle("Expected death age at challenges until reaching 100", y=1.04)
    return _finish(grid.fig, output_path or FIGURES_DIR / "03_challenge_curves.png")


def plot_hazard_comparison(df, output_path: str | Path | None = None):
    """Plot H(x) curves for two or more localities."""
    set_theme()
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.lineplot(data=df, x="age", y="H", hue="country", palette=VIRIDIS_CMAP, linewidth=1.8, ax=ax)
    ax.set(
        xlabel="Idade (x)",
        ylabel="Hazard acumulado H(x) = -log(lx)",
        title="Hazard acumulado de mortalidade - comparacao",
    )
    ax.legend(title="Localidade", loc="best")
    return _finish(fig, output_path or FIGURES_DIR / "04_hazard_nordeste_chile.png")


def plot_milestone_bars(milestones_long, output_path: str | Path | None = None):
    """Compare milestone ages with grouped bars."""
    set_theme()
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(
        data=milestones_long,
        x="k",
        y="age_at_k",
        hue="country",
        palette=VIRIDIS_CMAP,
        ax=ax,
    )
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", fontsize=8, padding=2)
    ax.set(
        xlabel="Numero de desafios acumulados (k)",
        ylabel="Idade em que H atinge k",
        title="Idade em que o hazard acumulado atinge H = k",
    )
    ax.legend(title="Localidade", loc="best")
    return _finish(fig, output_path or FIGURES_DIR / "05_milestone_bars.png")

