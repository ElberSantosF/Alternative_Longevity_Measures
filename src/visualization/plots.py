"""Matplotlib/Seaborn plots for local life table analyses."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
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
    sns.set_theme(style="whitegrid", context="notebook", font="DejaVu Sans")
    plt.rcParams.update(
        {
            "axes.edgecolor": "#d7dbe0",
            "axes.labelcolor": "#28323f",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 120,
            "grid.color": "#e8ebef",
            "grid.linewidth": 0.8,
            "legend.frameon": False,
            "text.color": "#28323f",
        }
    )


def plot_hazard_curves(df, output_path: str | Path | None = None):
    """Plot H(x) curves for two or more localities."""
    set_theme()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    sns.lineplot(
        data=df,
        x="age",
        y="H",
        hue="country",
        palette=VIRIDIS_CMAP,
        linewidth=2.4,
        ax=ax,
    )
    max_h = df["H"].max()
    for level in range(1, int(np.floor(max_h)) + 1):
        ax.axhline(level, color="#a7b0ba", linestyle=":", linewidth=1)
        ax.text(df["age"].max(), level, f" H={level}", va="bottom", color="#6c7682", fontsize=9)

    for country, group in df.sort_values("age").groupby("country"):
        last = group.dropna(subset=["H"]).tail(1)
        if not last.empty:
            ax.text(
                last["age"].iloc[0],
                last["H"].iloc[0],
                f"  {country}",
                va="center",
                fontsize=9,
            )

    ax.set(
        xlabel="Idade (x)",
        ylabel="Hazard acumulado H(x) = -log(l)",
        title="Hazard acumulado de mortalidade - comparacao",
    )
    ax.legend(title="Localidade", loc="upper left")
    return _finish(fig, output_path or FIGURES_DIR / "hazard_curves.png")


def plot_hazard_comparison(df, output_path: str | Path | None = None):
    """Backward-compatible alias for ``plot_hazard_curves``."""
    return plot_hazard_curves(df, output_path)


def plot_milestone_bars(milestones_long, output_path: str | Path | None = None):
    """Compare milestone ages with grouped bars."""
    set_theme()
    fig, ax = plt.subplots(figsize=(9, 5.2))
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
    return _finish(fig, output_path or FIGURES_DIR / "milestone_bars.png")


def plot_survival_curves(df, output_path: str | Path | None = None):
    """Plot normalized survival curves l(x)."""
    set_theme()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    sns.lineplot(
        data=df,
        x="age",
        y="l",
        hue="country",
        palette=VIRIDIS_CMAP,
        linewidth=2.4,
        ax=ax,
    )
    ax.axhline(np.exp(-1), color="#a7b0ba", linestyle="--", linewidth=1)
    ax.text(df["age"].max(), np.exp(-1), " l=e^-1", va="bottom", color="#6c7682", fontsize=9)
    ax.set(
        xlabel="Idade (x)",
        ylabel="Sobrevivencia normalizada l(x)",
        title="Funcao de sobrevivencia por idade",
    )
    ax.legend(title="Localidade", loc="lower left")
    return _finish(fig, output_path or FIGURES_DIR / "survival_curves.png")


def plot_fixed_age_hazards(indicators, output_path: str | Path | None = None):
    """Plot fixed-age cumulative hazards from the indicators table."""
    set_theme()
    h_cols = [col for col in indicators.columns if col.startswith("H_") and col[2:].isdigit()]
    plot_data = indicators.melt(
        id_vars=["country", "year"],
        value_vars=h_cols,
        var_name="age",
        value_name="H",
    ).dropna(subset=["H"])
    plot_data["age"] = plot_data["age"].str.replace("H_", "", regex=False).astype(int)

    fig, ax = plt.subplots(figsize=(9, 5.2))
    sns.lineplot(
        data=plot_data,
        x="age",
        y="H",
        hue="country",
        marker="o",
        palette=VIRIDIS_CMAP,
        linewidth=2.2,
        ax=ax,
    )
    ax.set(
        xlabel="Idade fixa",
        ylabel="H(x)",
        title="Hazard acumulado em idades fixas",
    )
    ax.legend(title="Localidade", loc="best")
    return _finish(fig, output_path or FIGURES_DIR / "fixed_age_hazards.png")


def plot_milestone_differences(differences, output_path: str | Path | None = None):
    """Plot milestone age differences against a reference location."""
    set_theme()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    sns.barplot(
        data=differences,
        x="k",
        y="difference_years",
        hue="country",
        palette=VIRIDIS_CMAP,
        ax=ax,
    )
    ax.axhline(0, color="#28323f", linewidth=1)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f", fontsize=8, padding=2)
    reference = differences["reference_country"].iloc[0] if not differences.empty else "referencia"
    ax.set(
        xlabel="Numero de desafios acumulados (k)",
        ylabel=f"Diferenca em anos vs {reference}",
        title="Diferenca nas idades de marcos H=k",
    )
    ax.legend(title="Localidade", loc="best")
    return _finish(fig, output_path or FIGURES_DIR / "milestone_differences.png")
