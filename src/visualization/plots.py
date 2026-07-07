"""Matplotlib/Seaborn plots for local life table analyses."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config.settings import FIGURES_DIR

PALETTE = ["#2F5D8C", "#7A8796", "#2F7D6D", "#A4554A", "#6F5B8B", "#B07C3E"]
TITLE_PAD = 14
BRAZIL_REGIONS = ("North Brazil", "Northeast Brazil")
SEX_ORDER = ("Female", "Male")
REPORT_INDICATORS = ("H_60", "H_70", "H_80", "H_90", "x_H1", "median_age", "e0_approx")
INDICATOR_LABELS = {
    "H_60": "Hazard at 60",
    "H_70": "Hazard at 70",
    "H_80": "Hazard at 80",
    "H_90": "Hazard at 90",
    "H_100": "Hazard at 100",
    "x_H1": "Age at H=1",
    "median_age": "Median age",
    "modal_age": "Modal age",
    "e0_approx": "Approx. e0",
    "e50_approx": "Approx. e50",
    "e90_approx": "Approx. e90",
}


def _palette_for(data, hue: str = "country"):
    levels = list(dict.fromkeys(data[hue].dropna()))
    return {level: PALETTE[index % len(PALETTE)] for index, level in enumerate(levels)}


def _label_indicator(value: str) -> str:
    return INDICATOR_LABELS.get(value, value.replace("_", " "))


def _ordered_categories(data: pd.DataFrame, category: str, value: str, *, ascending: bool = False):
    return (
        data.groupby(category, dropna=False)[value]
        .mean()
        .sort_values(ascending=ascending)
        .index
        .tolist()
    )


def _add_region_sex(data):
    out = data.copy()
    parts = out["country"].astype(str).str.rsplit(" - ", n=1, expand=True)
    out["region"] = parts[0]
    out["sex"] = parts[1] if parts.shape[1] > 1 else ""
    return out


def _brazil_region_data(data):
    out = _add_region_sex(data)
    return out.loc[out["region"].isin(BRAZIL_REGIONS)].copy()


def _finish(fig, output_path: str | Path | None = None):
    fig.tight_layout(pad=1.4)
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches="tight")
    return fig


def _legend_outside(ax, *, title: str = "Location", ncol: int = 1):
    """Move legends out of the plotting area and reserve space for them."""
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return None
    legend = ax.legend(
        handles=handles,
        labels=labels,
        title=title,
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        borderaxespad=0,
        frameon=True,
        ncol=ncol,
    )
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#d7dbe0")
    legend.get_frame().set_linewidth(0.8)
    ax.figure.subplots_adjust(right=0.78)
    return legend


def _style_axis(ax, *, title: str, xlabel: str, ylabel: str):
    ax.set_title(title, loc="left", pad=TITLE_PAD, fontweight="semibold")
    ax.set_xlabel(xlabel, labelpad=8)
    ax.set_ylabel(ylabel, labelpad=8)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e8ebef", linewidth=0.8)
    ax.margins(x=0.02)


def _add_bar_labels(ax, *, fmt: str = "%.1f", padding: int = 3):
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, fontsize=8, padding=padding, color="#44505e")


def _add_zero_line(ax, *, orientation: str = "vertical"):
    if orientation == "vertical":
        ax.axvline(0, color="#28323f", linewidth=1)
    else:
        ax.axhline(0, color="#28323f", linewidth=1)


def _style_facet_grid(grid):
    for ax in grid.axes.flat:
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", color="#e8ebef", linewidth=0.8)
        ax.set_title(ax.get_title(), pad=TITLE_PAD, fontweight="semibold")
        ax.margins(x=0.05)
    return grid


def _legend_for_grid(grid, *, title: str):
    if grid.legend is None:
        return None
    sns.move_legend(
        grid,
        "center left",
        bbox_to_anchor=(1.02, 0.5),
        title=title,
        frameon=True,
    )
    grid.legend.get_frame().set_facecolor("white")
    grid.legend.get_frame().set_edgecolor("#d7dbe0")
    grid.legend.get_frame().set_linewidth(0.8)
    grid.fig.subplots_adjust(right=0.74)
    return grid.legend


def set_theme() -> None:
    """Apply a minimal plotting theme."""
    sns.set_theme(style="whitegrid", context="notebook", font="DejaVu Sans", palette=PALETTE)
    plt.rcParams.update(
        {
            "axes.edgecolor": "#d7dbe0",
            "axes.labelcolor": "#28323f",
            "axes.titlecolor": "#18212f",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "figure.dpi": 120,
            "grid.color": "#e8ebef",
            "grid.linewidth": 0.8,
            "legend.frameon": True,
            "legend.borderaxespad": 0.8,
            "legend.fontsize": 9,
            "legend.title_fontsize": 9,
            "text.color": "#28323f",
            "xtick.color": "#44505e",
            "ytick.color": "#44505e",
        }
    )


def plot_hazard_curves(df, output_path: str | Path | None = None):
    """Plot H(x) curves for two or more localities."""
    set_theme()
    fig, ax = plt.subplots(figsize=(11.5, 6))
    sns.lineplot(
        data=df,
        x="age",
        y="H",
        hue="country",
        palette=_palette_for(df),
        linewidth=2.6,
        ax=ax,
    )
    max_h = df["H"].max()
    for level in range(1, int(np.floor(max_h)) + 1):
        ax.axhline(level, color="#b7c0ca", linestyle=":", linewidth=1, zorder=0)
        ax.text(
            df["age"].max() + 0.5,
            level,
            f"H={level}",
            ha="left",
            va="center",
            color="#6c7682",
            fontsize=8,
        )

    _style_axis(
        ax,
        xlabel="Age",
        ylabel="Cumulative hazard, H(x) = -log(l)",
        title="Cumulative mortality hazard",
    )
    ax.set_xlim(df["age"].min(), df["age"].max() + 4)
    _legend_outside(ax)
    return _finish(fig, output_path or FIGURES_DIR / "hazard_curves.png")


def plot_hazard_comparison(df, output_path: str | Path | None = None):
    """Backward-compatible alias for ``plot_hazard_curves``."""
    return plot_hazard_curves(df, output_path)


def plot_milestone_bars(milestones_long, output_path: str | Path | None = None):
    """Compare milestone ages with grouped bars."""
    set_theme()
    fig, ax = plt.subplots(figsize=(11, 5.8))
    sns.barplot(
        data=milestones_long,
        x="k",
        y="age_at_k",
        hue="country",
        palette=_palette_for(milestones_long),
        ax=ax,
    )
    _add_bar_labels(ax)
    ax.set_ylim(top=milestones_long["age_at_k"].max() + 5)
    _style_axis(
        ax,
        xlabel="Number of accumulated challenges (k)",
        ylabel="Age when H reaches k",
        title="Age when cumulative hazard reaches H = k",
    )
    _legend_outside(ax)
    return _finish(fig, output_path or FIGURES_DIR / "milestone_bars.png")


def plot_survival_curves(df, output_path: str | Path | None = None):
    """Plot normalized survival curves l(x)."""
    set_theme()
    fig, ax = plt.subplots(figsize=(11.5, 6))
    sns.lineplot(
        data=df,
        x="age",
        y="l",
        hue="country",
        palette=_palette_for(df),
        linewidth=2.6,
        ax=ax,
    )
    ax.axhline(np.exp(-1), color="#a7b0ba", linestyle="--", linewidth=1)
    ax.annotate(
        "l=e^-1",
        xy=(1, np.exp(-1)),
        xycoords=("axes fraction", "data"),
        xytext=(-4, 4),
        textcoords="offset points",
        ha="right",
        va="bottom",
        color="#6c7682",
        fontsize=8,
    )
    _style_axis(
        ax,
        xlabel="Age",
        ylabel="Normalized survival l(x)",
        title="Survival function by age",
    )
    ax.set_ylim(-0.02, 1.02)
    _legend_outside(ax)
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

    fig, ax = plt.subplots(figsize=(11, 5.8))
    sns.lineplot(
        data=plot_data,
        x="age",
        y="H",
        hue="country",
        marker="o",
        palette=_palette_for(plot_data),
        linewidth=2.4,
        markersize=7,
        ax=ax,
    )
    _style_axis(
        ax,
        xlabel="Fixed age",
        ylabel="H(x)",
        title="Cumulative hazard at fixed ages",
    )
    _legend_outside(ax)
    return _finish(fig, output_path or FIGURES_DIR / "fixed_age_hazards.png")


def plot_milestone_differences(differences, output_path: str | Path | None = None):
    """Plot milestone age differences against a reference location."""
    set_theme()
    fig, ax = plt.subplots(figsize=(11, 5.4))
    sns.barplot(
        data=differences,
        x="k",
        y="difference_years",
        hue="country",
        palette=_palette_for(differences),
        ax=ax,
    )
    ax.axhline(0, color="#28323f", linewidth=1)
    _add_bar_labels(ax)
    reference = differences["reference_country"].iloc[0] if not differences.empty else "reference"
    y_values = differences["difference_years"].dropna()
    if not y_values.empty:
        pad = max((y_values.max() - y_values.min()) * 0.12, 1)
        ax.set_ylim(y_values.min() - pad, y_values.max() + pad)
    _style_axis(
        ax,
        xlabel="Number of accumulated challenges (k)",
        ylabel=f"Difference in years vs {reference}",
        title="Difference in H=k milestone ages",
    )
    _legend_outside(ax)
    return _finish(fig, output_path or FIGURES_DIR / "milestone_differences.png")


def plot_correlation_heatmap(correlations, output_path: str | Path | None = None):
    """Plot a correlation matrix for longevity indicators."""
    set_theme()
    labeled = correlations.rename(index=_label_indicator, columns=_label_indicator)
    fig, ax = plt.subplots(figsize=(9.5, 8))
    sns.heatmap(
        labeled,
        vmin=-1,
        vmax=1,
        center=0,
        cmap="vlag",
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.8,
        linecolor="white",
        cbar_kws={"label": "correlation"},
        ax=ax,
    )
    ax.set_title("Correlation among longevity indicators", loc="left", pad=TITLE_PAD, fontweight="semibold")
    ax.tick_params(axis="x", rotation=35, labelsize=9)
    ax.tick_params(axis="y", rotation=0)
    return _finish(fig, output_path or FIGURES_DIR / "indicator_correlations.png")


def plot_indicator_scatter(indicators, output_path: str | Path | None = None):
    """Plot conventional indicators against H_max."""
    set_theme()
    value_cols = [
        col
        for col in ("e0_approx", "e50_approx", "modal_age", "median_age", "x_H1")
        if col in indicators.columns
    ]
    plot_data = indicators.melt(
        id_vars=["country", "year", "H_max"],
        value_vars=value_cols,
        var_name="indicator",
        value_name="value",
    ).dropna(subset=["H_max", "value"])
    plot_data["indicator_label"] = plot_data["indicator"].map(_label_indicator)

    grid = sns.relplot(
        data=plot_data,
        x="value",
        y="H_max",
        hue="country",
        col="indicator_label",
        col_wrap=3,
        palette=_palette_for(plot_data),
        height=3.5,
        aspect=1.12,
        s=70,
        edgecolor="white",
        linewidth=0.8,
        facet_kws={"sharex": False, "sharey": True},
    )
    grid.set_axis_labels("Indicator value", "H_max")
    grid.set_titles("{col_name}")
    for ax in grid.axes.flat:
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", color="#e8ebef", linewidth=0.8)
    if grid.legend is not None:
        grid.legend.set_title("Location")
        grid.legend.set_bbox_to_anchor((1.02, 0.95))
        grid.legend._loc = 2
        grid.legend.get_frame().set_facecolor("white")
        grid.legend.get_frame().set_edgecolor("#d7dbe0")
    grid.fig.subplots_adjust(top=0.88, right=0.82, wspace=0.25, hspace=0.32)
    grid.fig.suptitle(
        "Conventional indicators vs maximum cumulative hazard",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "indicator_scatter.png")


def plot_indicator_rankings(rankings, output_path: str | Path | None = None):
    """Plot ranking positions for selected longevity indicators."""
    set_theme()
    rank_cols = [col for col in rankings.columns if col.startswith("rank_")]
    plot_data = rankings.melt(
        id_vars=["country", "year"],
        value_vars=rank_cols,
        var_name="indicator",
        value_name="rank",
    ).dropna(subset=["rank"])
    plot_data["indicator"] = plot_data["indicator"].str.replace("rank_", "", regex=False)
    plot_data["indicator_label"] = plot_data["indicator"].map(_label_indicator)

    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    sns.lineplot(
        data=plot_data,
        x="indicator_label",
        y="rank",
        hue="country",
        marker="o",
        palette=_palette_for(plot_data),
        linewidth=2.3,
        markersize=7,
        ax=ax,
    )
    ax.invert_yaxis()
    _style_axis(
        ax,
        xlabel="Indicator",
        ylabel="Ranking (1 = best)",
        title="Comparative ranking by indicator",
    )
    ax.tick_params(axis="x", rotation=20)
    _legend_outside(ax)
    return _finish(fig, output_path or FIGURES_DIR / "indicator_rankings.png")


def plot_regional_hazard_by_sex(df, output_path: str | Path | None = None):
    """Compare cumulative hazard for North and Northeast, faceted by sex."""
    set_theme()
    plot_data = _brazil_region_data(df)
    grid = sns.relplot(
        data=plot_data,
        x="age",
        y="H",
        hue="region",
        col="sex",
        col_order=[sex for sex in SEX_ORDER if sex in plot_data["sex"].unique()],
        kind="line",
        palette=_palette_for(plot_data, "region"),
        linewidth=2.6,
        height=4.2,
        aspect=1.2,
        facet_kws={"sharey": True},
    )
    grid.set_axis_labels("Age (x)", "Cumulative hazard H(x)")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    _legend_for_grid(grid, title="Region")
    grid.fig.subplots_adjust(top=0.82, right=0.78, wspace=0.18)
    grid.fig.suptitle(
        "North vs Northeast: cumulative hazard by sex",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "regional_hazard_by_sex.png")


def plot_regional_survival_by_sex(df, output_path: str | Path | None = None):
    """Compare normalized survival for North and Northeast, faceted by sex."""
    set_theme()
    plot_data = _brazil_region_data(df)
    grid = sns.relplot(
        data=plot_data,
        x="age",
        y="l",
        hue="region",
        col="sex",
        col_order=[sex for sex in SEX_ORDER if sex in plot_data["sex"].unique()],
        kind="line",
        palette=_palette_for(plot_data, "region"),
        linewidth=2.6,
        height=4.2,
        aspect=1.2,
        facet_kws={"sharey": True},
    )
    grid.set_axis_labels("Age (x)", "Normalized survival l(x)")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    _legend_for_grid(grid, title="Region")
    grid.fig.subplots_adjust(top=0.82, right=0.78, wspace=0.18)
    grid.fig.suptitle(
        "North vs Northeast: survival by sex",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "regional_survival_by_sex.png")


def plot_regional_hazard_gap_by_sex(df, output_path: str | Path | None = None):
    """Plot H_North - H_Northeast by age for each sex."""
    set_theme()
    plot_data = _brazil_region_data(df)
    wide = plot_data.pivot_table(index=["sex", "age"], columns="region", values="H").reset_index()
    wide["gap"] = wide["North Brazil"] - wide["Northeast Brazil"]

    fig, ax = plt.subplots(figsize=(11, 5.8))
    sns.lineplot(
        data=wide.dropna(subset=["gap"]),
        x="age",
        y="gap",
        hue="sex",
        hue_order=[sex for sex in SEX_ORDER if sex in wide["sex"].unique()],
        palette=_palette_for(wide, "sex"),
        linewidth=2.6,
        ax=ax,
    )
    ax.axhline(0, color="#28323f", linewidth=1)
    _style_axis(
        ax,
        xlabel="Age (x)",
        ylabel="Cumulative hazard difference",
        title="Regional gap: H_North - H_Northeast",
    )
    _legend_outside(ax, title="Sex")
    return _finish(fig, output_path or FIGURES_DIR / "regional_hazard_gap_by_sex.png")


def plot_sex_hazard_gap_by_region(df, output_path: str | Path | None = None):
    """Plot H_male - H_female by age for North and Northeast."""
    set_theme()
    plot_data = _brazil_region_data(df)
    wide = plot_data.pivot_table(index=["region", "age"], columns="sex", values="H").reset_index()
    wide["gap"] = wide["Male"] - wide["Female"]

    fig, ax = plt.subplots(figsize=(11, 5.8))
    sns.lineplot(
        data=wide.dropna(subset=["gap"]),
        x="age",
        y="gap",
        hue="region",
        palette=_palette_for(wide, "region"),
        linewidth=2.6,
        ax=ax,
    )
    ax.axhline(0, color="#28323f", linewidth=1)
    _style_axis(
        ax,
        xlabel="Age (x)",
        ylabel="Cumulative hazard difference",
        title="Sex gap: H_male - H_female",
    )
    _legend_outside(ax, title="Region")
    return _finish(fig, output_path or FIGURES_DIR / "sex_hazard_gap_by_region.png")


def plot_benchmark_hazard_gap_vs_chile(df, output_path: str | Path | None = None):
    """Plot Brazilian regional hazard gaps against Chile, by sex."""
    set_theme()
    selected = _add_region_sex(df)
    selected = selected.loc[selected["region"].isin((*BRAZIL_REGIONS, "Chile"))].copy()
    wide = selected.pivot_table(index=["sex", "age"], columns="region", values="H").reset_index()
    rows = []
    for region in BRAZIL_REGIONS:
        temp = wide[["sex", "age", "Chile", region]].copy()
        temp["region"] = region
        temp["gap"] = temp[region] - temp["Chile"]
        rows.append(temp[["sex", "age", "region", "gap"]])
    plot_data = pd.concat(rows, ignore_index=True).dropna(subset=["gap"])

    grid = sns.relplot(
        data=plot_data,
        x="age",
        y="gap",
        hue="region",
        col="sex",
        col_order=[sex for sex in SEX_ORDER if sex in plot_data["sex"].unique()],
        kind="line",
        palette=_palette_for(plot_data, "region"),
        linewidth=2.6,
        height=4.2,
        aspect=1.2,
        facet_kws={"sharey": True},
    )
    for ax in grid.axes.flat:
        ax.axhline(0, color="#28323f", linewidth=1)
    grid.set_axis_labels("Age (x)", "Cumulative hazard difference vs Chile")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    for ax in grid.axes.flat:
        ax.set_xlabel("Age")
    _legend_for_grid(grid, title="Region")
    grid.fig.subplots_adjust(top=0.82, right=0.78, wspace=0.18)
    grid.fig.suptitle(
        "External benchmark: Brazilian regions vs Chile",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "benchmark_hazard_gap_vs_chile.png")


def plot_indicator_heatmap_standardized(indicators, output_path: str | Path | None = None):
    """Plot standardized indicator values for all groups."""
    set_theme()
    columns = [col for col in REPORT_INDICATORS if col in indicators.columns]
    values = indicators.set_index("country")[columns].copy()
    standardized = (values - values.mean()) / values.std(ddof=0)
    values = values.rename(columns=_label_indicator)
    standardized = standardized.rename(columns=_label_indicator)

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    sns.heatmap(
        standardized,
        cmap="vlag",
        center=0,
        linewidths=0.8,
        linecolor="white",
        annot=values,
        fmt=".1f",
        cbar_kws={"label": "standardized value"},
        ax=ax,
    )
    ax.set_title("Standardized indicator summary", loc="left", pad=TITLE_PAD, fontweight="semibold")
    ax.set_xlabel("Indicator")
    ax.set_ylabel("Location")
    ax.tick_params(axis="x", rotation=30)
    ax.tick_params(axis="y", rotation=0)
    return _finish(fig, output_path or FIGURES_DIR / "indicator_heatmap_standardized.png")


def plot_indicator_bars_brazil_regions(indicators, output_path: str | Path | None = None):
    """Plot selected indicators for North and Northeast only."""
    set_theme()
    plot_data = _brazil_region_data(indicators)
    columns = [col for col in REPORT_INDICATORS if col in plot_data.columns]
    long = plot_data.melt(
        id_vars=["country", "region", "sex"],
        value_vars=columns,
        var_name="indicator",
        value_name="value",
    ).dropna(subset=["value"])
    long["indicator_label"] = long["indicator"].map(_label_indicator)

    grid = sns.catplot(
        data=long,
        x="value",
        y="country",
        hue="sex",
        col="indicator_label",
        col_wrap=3,
        kind="bar",
        palette=_palette_for(long, "sex"),
        height=3.2,
        aspect=1.25,
        sharex=False,
        sharey=True,
    )
    grid.set_axis_labels("Value", "Location")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    _legend_for_grid(grid, title="Sex")
    grid.fig.subplots_adjust(top=0.88, right=0.78, wspace=0.42, hspace=0.35)
    grid.fig.suptitle(
        "Selected indicators: North and Northeast",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "indicator_bars_brazil_regions.png")


def plot_conditional_survival(conditional_survival, output_path: str | Path | None = None):
    """Plot conditional survival probabilities by transition age."""
    set_theme()
    plot_data = conditional_survival.dropna(subset=["conditional_survival"]).copy()
    plot_data["conditional_survival_pct"] = plot_data["conditional_survival"] * 100
    order = _ordered_categories(plot_data, "country", "conditional_survival_pct", ascending=False)

    grid = sns.catplot(
        data=plot_data,
        x="conditional_survival_pct",
        y="country",
        order=order,
        hue="country",
        col="transition",
        col_wrap=2,
        kind="bar",
        palette=_palette_for(plot_data),
        height=3.4,
        aspect=1.35,
        sharex=False,
        sharey=True,
        legend=False,
    )
    grid.set_axis_labels("Survival probability (%)", "")
    grid.set_titles("{col_name} years")
    _style_facet_grid(grid)
    for ax in grid.axes.flat:
        _add_bar_labels(ax, fmt="%.1f", padding=4)
        ax.set_xlim(right=ax.get_xlim()[1] * 1.08)
    grid.fig.subplots_adjust(top=0.88, wspace=0.24, hspace=0.35)
    grid.fig.suptitle(
        "Probability of surviving between selected ages",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "conditional_survival.png")


def plot_age_band_hazard_contributions(age_band_contributions, output_path: str | Path | None = None):
    """Plot cumulative hazard increments by age band."""
    set_theme()
    plot_data = age_band_contributions.dropna(subset=["hazard_increment"]).copy()
    order = list(dict.fromkeys(plot_data["age_band"]))

    grid = sns.catplot(
        data=plot_data,
        x="age_band",
        y="hazard_increment",
        order=order,
        hue="country",
        col="country",
        col_wrap=2,
        kind="bar",
        palette=_palette_for(plot_data),
        height=3.4,
        aspect=1.35,
        sharey=False,
        legend=False,
    )
    grid.set_axis_labels("Age band", "H increment")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    for ax in grid.axes.flat:
        ax.tick_params(axis="x", rotation=25)
        _add_bar_labels(ax, fmt="%.2f")
    grid.fig.subplots_adjust(top=0.88, wspace=0.28, hspace=0.42)
    grid.fig.suptitle(
        "Age-band contribution to cumulative hazard",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "age_band_hazard_contributions.png")


def plot_sex_indicator_gaps(sex_gaps, output_path: str | Path | None = None):
    """Plot female-minus-male gaps for selected indicators."""
    set_theme()
    plot_data = sex_gaps.dropna(subset=["gap_female_minus_male"]).copy()
    plot_data["indicator_label"] = plot_data["indicator"].map(_label_indicator)
    order = _ordered_categories(plot_data, "region", "gap_female_minus_male", ascending=False)

    grid = sns.catplot(
        data=plot_data,
        x="gap_female_minus_male",
        y="region",
        order=order,
        hue="region",
        col="indicator_label",
        col_wrap=3,
        kind="bar",
        palette=_palette_for(plot_data, "region"),
        height=3.2,
        aspect=1.25,
        sharex=False,
        sharey=True,
        legend=False,
    )
    grid.set_axis_labels("Female - male", "")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    for ax in grid.axes.flat:
        _add_zero_line(ax)
        _add_bar_labels(ax, fmt="%.2f")
        left, right = ax.get_xlim()
        span = right - left
        ax.set_xlim(left - span * 0.04, right + span * 0.08)
    grid.fig.subplots_adjust(top=0.88, wspace=0.35, hspace=0.35)
    grid.fig.suptitle(
        "Female-male gap in longevity indicators",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "sex_indicator_gaps.png")
