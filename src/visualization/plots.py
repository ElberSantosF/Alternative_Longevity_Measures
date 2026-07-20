"""Report- and presentation-ready plots for local life table analyses."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import seaborn as sns

from src.config.settings import MAX_ANALYSIS_AGE
from src.visualization.style import (
    ALL_REGION_ORDER,
    DISPLAY_LABELS_PT,
    GRID,
    MUTED,
    PROFILES,
    REGION_COLORS,
    REGION_ORDER,
    SEX_COLORS,
    SEX_MARKERS,
    SEX_ORDER,
    TEXT,
    ZERO,
    FigureProfile,
    add_header,
    apply_theme,
    decimal_formatter,
    display_label,
    finish_figure,
    format_pt,
    get_profile,
    indicator_label,
    style_axis,
)

PALETTE = list(REGION_COLORS.values())
REPORT_COLORS = {**REGION_COLORS, **SEX_COLORS}
BAR_PALETTE = PALETTE
BAR_COLORS = REPORT_COLORS
TITLE_PAD = 14
BRAZIL_REGIONS = REGION_ORDER
REPORT_INDICATORS = ("H_60", "H_80", "H_90", "x_H1", "median_age", "e0_approx")
INDICATOR_LABELS = {
    key: indicator_label(key)
    for key in (*REPORT_INDICATORS, "H_70", "e50_approx")
}
DISPLAY_LABELS = DISPLAY_LABELS_PT

def _palette_for(data, hue: str = "country"):
    levels = list(dict.fromkeys(data[hue].dropna()))
    return {
        level: REPORT_COLORS.get(
            level,
            REGION_COLORS.get(str(level).rsplit(" - ", 1)[0], PALETTE[index % len(PALETTE)]),
        )
        for index, level in enumerate(levels)
    }


def _bar_palette_for(data, hue: str = "country"):
    return _palette_for(data, hue)


def _label_indicator(value: str) -> str:
    return indicator_label(value)


def _display_label(value) -> str:
    return display_label(value)


def _translate_text(value: str) -> str:
    translated = value
    for raw, label in sorted(DISPLAY_LABELS_PT.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(raw, label)
    translated = translated.replace("sex = ", "").replace("region = ", "")
    return translated


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


def _analysis_age_data(data, age_col: str = "age"):
    if age_col not in data.columns:
        return data.copy()
    return data.loc[data[age_col] <= MAX_ANALYSIS_AGE].copy()


def _brazil_region_data(data):
    out = _add_region_sex(_analysis_age_data(data))
    return out.loc[out["region"].isin(BRAZIL_REGIONS)].copy()


def _finish(
    fig,
    output_path: str | Path | None = None,
    *,
    note: str | None = None,
    source: str = "Fonte: elaboração própria com base nas tábuas de vida registradas no projeto.",
):
    if not hasattr(fig, "_figure_profile"):
        fig._figure_profile = PROFILES["report"]
    if not getattr(fig, "_layout_finalized", False):
        fig.tight_layout(pad=1.2, rect=(0.04, 0.09, 0.97, 0.9))
    return finish_figure(
        fig,
        output_path,
        note=note
        or rf"Nota: análise limitada a {MAX_ANALYSIS_AGE} anos; $H(x)=-\ln[\ell(x)]$.",
        source=source,
    )


def _legend_outside(ax, *, title: str = "Localidade", ncol: int = 1):
    """Move legends out of the plotting area and reserve space for them."""
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return None
    legend = ax.legend(
        handles=handles,
        labels=[_display_label(label) for label in labels],
        title=title,
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        borderaxespad=0,
        frameon=True,
        ncol=ncol,
    )
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor(GRID)
    legend.get_frame().set_linewidth(0.8)
    ax.figure.subplots_adjust(right=0.78)
    return legend


def _style_axis(ax, *, title: str, xlabel: str, ylabel: str):
    ax.set_title(title, loc="left", pad=TITLE_PAD, fontweight="semibold", fontsize=13)
    style_axis(ax, xlabel=xlabel, ylabel=ylabel, grid_axis="y")
    ax.margins(x=0.02)


def _add_bar_labels(ax, *, fmt: str = "%.1f", padding: int = 3):
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, fontsize=8.5, padding=padding, color=MUTED)


def _add_zero_line(ax, *, orientation: str = "vertical"):
    if orientation == "vertical":
        ax.axvline(0, color=ZERO, linewidth=1)
    else:
        ax.axhline(0, color=ZERO, linewidth=1)


def _style_facet_grid(grid):
    for ax in grid.axes.flat:
        style_axis(ax, xlabel=ax.get_xlabel(), ylabel=ax.get_ylabel(), grid_axis="y")
        ax.set_title(_translate_text(ax.get_title()), pad=TITLE_PAD, fontweight="semibold", fontsize=12)
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
    grid.legend.get_frame().set_edgecolor(GRID)
    grid.legend.get_frame().set_linewidth(0.8)
    for text in grid.legend.texts:
        text.set_text(_display_label(text.get_text()))
    grid.fig.subplots_adjust(right=0.74)
    return grid.legend


def set_theme(profile: str | FigureProfile = "report") -> FigureProfile:
    """Apply the shared visual identity (kept as a public compatibility helper)."""

    return apply_theme(profile)


def _require_columns(data: pd.DataFrame, required: tuple[str, ...], chart: str) -> None:
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"{chart}: colunas ausentes: {', '.join(missing)}")


def _new_subplots(
    profile: str | FigureProfile,
    *,
    nrows: int = 1,
    ncols: int = 1,
    sharex: bool = False,
    sharey: bool = False,
    size: str = "standard",
    squeeze: bool = True,
):
    spec = set_theme(profile)
    sizes = {
        "standard": spec.figsize,
        "wide": (8.2, 4.6) if spec.name == "report" else spec.figsize,
        "grid": (7.2, 6.6) if spec.name == "report" else spec.figsize,
        "tall": (7.2, 7.6) if spec.name == "report" else (12.0, 8.4),
    }
    fig, axes = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        sharex=sharex,
        sharey=sharey,
        figsize=sizes[size],
        squeeze=squeeze,
    )
    fig._figure_profile = spec
    return fig, axes, spec


def _period_text(data: pd.DataFrame) -> str:
    if "year" not in data.columns:
        return ""
    if "country" in data.columns:
        locations = data["country"].astype(str).str.rsplit(" - ", n=1).str[0]
    elif "region" in data.columns:
        locations = data["region"].astype(str)
    else:
        locations = pd.Series("", index=data.index)

    frame = pd.DataFrame({"location": locations, "year": data["year"]}).dropna(subset=["year"])
    parts: list[str] = []
    brazil_years = sorted(frame.loc[frame["location"].isin(REGION_ORDER), "year"].astype(int).unique())
    chile_years = sorted(frame.loc[frame["location"] == "Chile", "year"].astype(int).unique())
    if brazil_years:
        parts.append(f"Brasil ({'/'.join(map(str, brazil_years))})")
    if chile_years:
        parts.append(f"Chile ({'/'.join(map(str, chile_years))})")
    if not parts:
        years = sorted(frame["year"].astype(int).unique())
        return f"Ano(s): {'/'.join(map(str, years))}" if years else ""
    return " e ".join(parts)


def _subtitle(data: pd.DataFrame, *, profile: FigureProfile, extra: str = "") -> str:
    parts = ["Tábuas de vida de período"]
    period = _period_text(data)
    if period:
        parts.append(period)
    if profile.name == "slides" and "age" in data.columns:
        parts.append("recorte visual de 40 a 90 anos")
    if extra:
        parts.append(extra)
    return " • ".join(parts)


def _method_note(
    *,
    include_h: bool = True,
    comparison_warning: bool = False,
    extra: str = "",
) -> str:
    parts = [f"Nota: análise limitada a {MAX_ANALYSIS_AGE} anos"]
    if include_h:
        parts.append(r"$H(x)=-\ln[\ell(x)]$")
    if comparison_warning:
        parts.append("comparação Brasil–Chile é descritiva, pois os anos de referência diferem")
    if extra:
        parts.append(extra)
    return "; ".join(parts) + "."


def _analysis_start_age(spec: FigureProfile) -> int:
    return 40 if spec.name == "slides" else 0


def _order_intervals(intervals: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Place component intervals chronologically and any encompassing total last."""

    def is_total(interval: tuple[float, float]) -> bool:
        start, end = interval
        others = [other for other in intervals if other != interval]
        return bool(others) and all(start <= other[0] and end >= other[1] for other in others)

    return sorted(intervals, key=lambda interval: (is_total(interval), interval[0], interval[1]))


def _top_legend(fig, handles, labels, *, ncol: int = 3, y: float | None = None):
    spec = fig._figure_profile
    if y is None:
        y = 0.815 - max(getattr(fig, "_subtitle_lines", 1) - 1, 0) * 0.035
    return fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.52, y),
        ncol=ncol,
        frameon=False,
        fontsize=spec.legend_size,
        columnspacing=1.5,
        handlelength=2.3,
        handletextpad=0.5,
    )


def _region_legend(fig, regions, *, y: float | None = None):
    handles = [
        Line2D(
            [0],
            [0],
            color=REGION_COLORS[region],
            linewidth=fig._figure_profile.line_width,
            linestyle=(0, (4, 2)) if region == "Chile" else "-",
            marker="o",
            markersize=fig._figure_profile.marker_size,
        )
        for region in regions
    ]
    return _top_legend(fig, handles, [_display_label(region) for region in regions], ncol=3, y=y)


def _sex_legend(fig, sexes, *, y: float | None = None):
    handles = [
        Line2D(
            [0],
            [0],
            color=SEX_COLORS[sex],
            marker=SEX_MARKERS[sex],
            linestyle="",
            markersize=fig._figure_profile.marker_size + 1,
        )
        for sex in sexes
    ]
    return _top_legend(fig, handles, [_display_label(sex) for sex in sexes], ncol=len(sexes), y=y)


def _finalize_layout(
    fig,
    *,
    left: float = 0.09,
    right: float = 0.97,
    bottom: float = 0.15,
    top: float = 0.79,
    wspace: float = 0.16,
    hspace: float = 0.34,
) -> None:
    if getattr(fig, "_subtitle_lines", 1) > 1:
        top = min(top, 0.66)
    fig.subplots_adjust(
        left=left,
        right=right,
        bottom=bottom,
        top=top,
        wspace=wspace,
        hspace=hspace,
    )
    fig._layout_finalized = True


def _validate_unique_series(data: pd.DataFrame, chart: str) -> None:
    keys = [column for column in ("region", "sex", "age") if column in data.columns]
    if keys and data.duplicated(keys, keep=False).any():
        raise ValueError(
            f"{chart}: há mais de uma observação por {'/'.join(keys)}; "
            "filtre um único ano antes de traçar as curvas."
        )


def _plot_curves_by_sex(
    df: pd.DataFrame,
    *,
    value: str,
    regions: tuple[str, ...],
    title: str,
    ylabel: str,
    output_path: str | Path | None,
    profile: str | FigureProfile,
    reference: float | None = None,
    comparison_warning: bool = False,
):
    _require_columns(df, ("country", "year", "age", value), title)
    plot_data = _add_region_sex(_analysis_age_data(df))
    plot_data = plot_data.loc[plot_data["region"].isin(regions)].copy()
    _validate_unique_series(plot_data, title)
    present_sexes = [sex for sex in SEX_ORDER if sex in plot_data["sex"].unique()]
    if not present_sexes:
        raise ValueError(f"{title}: nenhum sexo reconhecido nos rótulos de country.")

    fig, axes, spec = _new_subplots(
        profile,
        ncols=len(present_sexes),
        sharex=True,
        sharey=True,
        size="wide",
        squeeze=False,
    )
    axes = axes.ravel()
    start_age = _analysis_start_age(spec)
    present_regions = [region for region in regions if region in plot_data["region"].unique()]

    for ax, sex in zip(axes, present_sexes):
        for region in present_regions:
            series = plot_data.loc[
                (plot_data["sex"] == sex) & (plot_data["region"] == region)
            ].sort_values("age")
            if series.empty:
                continue
            ax.plot(
                series["age"],
                series[value],
                color=REGION_COLORS[region],
                linewidth=spec.line_width + (0.35 if region == "Chile" else 0),
                linestyle=(0, (4, 2)) if region == "Chile" else "-",
                marker="o",
                markersize=spec.marker_size,
                markeredgecolor="white",
                markeredgewidth=0.55,
                zorder=3,
            )
        if reference is not None:
            ax.axhline(reference, color=MUTED, linewidth=1, linestyle=(0, (2, 2)), zorder=1)
            label = r"$H(x)=1$" if value == "H" else r"$\ell(x)=e^{-1}$"
            ax.text(
                0.985,
                reference,
                label,
                transform=ax.get_yaxis_transform(),
                ha="right",
                va="bottom",
                color=MUTED,
                fontsize=spec.note_size,
            )
        style_axis(ax, xlabel="Idade (anos)", ylabel=ylabel if ax is axes[0] else "", grid_axis="y")
        ax.set_title(_display_label(sex), fontweight="semibold", pad=8)
        ax.set_xlim(start_age, MAX_ANALYSIS_AGE)
        ax.set_xticks([40, 50, 60, 70, 80, 90] if start_age else [0, 20, 40, 60, 80, 90])
        ax.yaxis.set_major_formatter(decimal_formatter(2 if value == "H" else 1))
        if value == "l":
            ax.set_ylim(0, 1.02)

    add_header(fig, title, _subtitle(plot_data, profile=spec))
    _region_legend(fig, present_regions)
    _finalize_layout(fig, left=0.085, right=0.975, bottom=0.16, top=0.70, wspace=0.12)
    return _finish(
        fig,
        output_path,
        note=_method_note(include_h=True, comparison_warning=comparison_warning),
    )


def _direct_line_labels(
    ax,
    data: pd.DataFrame,
    *,
    category: str,
    x: str,
    y: str,
    colors: dict[str, str],
    x_offset: float = 2.0,
) -> None:
    """Label line endpoints with light collision avoidance."""

    endpoints = (
        data.sort_values(x)
        .groupby(category, sort=False, as_index=False)
        .tail(1)[[category, x, y]]
        .dropna()
        .sort_values(y)
    )
    if endpoints.empty:
        return
    y_values = endpoints[y].to_numpy(float)
    axis_low, axis_high = ax.get_ylim()
    min_gap = max((axis_high - axis_low) * 0.055, np.finfo(float).eps)
    adjusted = y_values.copy()
    for index in range(1, len(adjusted)):
        adjusted[index] = max(adjusted[index], adjusted[index - 1] + min_gap)
    overflow = adjusted[-1] - (axis_high - min_gap * 0.3)
    if overflow > 0:
        adjusted -= overflow

    for (_, row), label_y in zip(endpoints.iterrows(), adjusted):
        level = row[category]
        ax.annotate(
            _display_label(level),
            xy=(row[x], row[y]),
            xytext=(row[x] + x_offset, label_y),
            textcoords="data",
            ha="left",
            va="center",
            color=colors[level],
            fontsize=ax.figure._figure_profile.legend_size,
            fontweight="semibold",
            arrowprops={
                "arrowstyle": "-",
                "color": colors[level],
                "linewidth": 0.8,
                "shrinkA": 1,
                "shrinkB": 2,
            },
            annotation_clip=False,
        )


def plot_hazard_curves(
    df,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Risco acumulado de mortalidade por idade",
):
    """Plot cumulative hazard in sex facets with one stable color per region."""

    return _plot_curves_by_sex(
        df,
        value="H",
        regions=ALL_REGION_ORDER,
        title=title,
        ylabel=r"Risco acumulado, $H(x)$",
        output_path=output_path,
        profile=profile,
        reference=1.0,
        comparison_warning=True,
    )


def plot_hazard_comparison(
    df,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
):
    """Backward-compatible alias for ``plot_hazard_curves``."""
    return plot_hazard_curves(df, output_path, profile=profile)


def plot_milestone_bars(milestones_long, output_path: str | Path | None = None):
    """Compare milestone ages with grouped bars."""
    set_theme()
    fig, ax = plt.subplots(figsize=(11, 5.8))
    sns.barplot(
        data=milestones_long,
        x="k",
        y="age_at_k",
        hue="country",
        palette=_bar_palette_for(milestones_long),
        ax=ax,
    )
    _add_bar_labels(ax)
    ax.set_ylim(top=milestones_long["age_at_k"].max() + 5)
    _style_axis(
        ax,
        xlabel="Cumulative hazard level (k)",
        ylabel="Age when H reaches k",
        title="Age at cumulative hazard milestones",
    )
    _legend_outside(ax)
    return _finish(fig, output_path)


def plot_survival_curves(
    df,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Sobrevivência até cada idade",
):
    """Plot normalized survival in sex facets with one stable color per region."""

    return _plot_curves_by_sex(
        df,
        value="l",
        regions=ALL_REGION_ORDER,
        title=title,
        ylabel=r"Proporção de sobreviventes, $\ell(x)$",
        output_path=output_path,
        profile=profile,
        reference=float(np.exp(-1)),
        comparison_warning=True,
    )


def plot_fixed_age_hazards(indicators, output_path: str | Path | None = None):
    """Plot fixed-age cumulative hazards from the indicators table."""
    set_theme()
    h_cols = [
        col
        for col in indicators.columns
        if col.startswith("H_") and col[2:].isdigit() and int(col[2:]) <= MAX_ANALYSIS_AGE
    ]
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
        xlabel="Reference age",
        ylabel="Cumulative hazard, H(x)",
        title="Cumulative hazard at selected ages",
    )
    _legend_outside(ax)
    return _finish(fig, output_path)


def plot_milestone_differences(differences, output_path: str | Path | None = None):
    """Plot milestone age differences against a reference location."""
    set_theme()
    fig, ax = plt.subplots(figsize=(11, 5.4))
    sns.barplot(
        data=differences,
        x="k",
        y="difference_years",
        hue="country",
        palette=_bar_palette_for(differences),
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
        xlabel="Cumulative hazard level (k)",
        ylabel=f"Difference in years vs {_display_label(reference)}",
        title="Age difference at H = k milestones",
    )
    _legend_outside(ax)
    return _finish(fig, output_path)


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
        cbar_kws={"label": "Correlation"},
        ax=ax,
    )
    ax.set_title("Correlation among longevity indicators", loc="left", pad=TITLE_PAD, fontweight="semibold")
    ax.tick_params(axis="x", rotation=35, labelsize=9)
    ax.tick_params(axis="y", rotation=0)
    return _finish(fig, output_path)


def plot_indicator_scatter(indicators, output_path: str | Path | None = None):
    """Plot conventional indicators against H_max."""
    set_theme()
    value_cols = [
        col
        for col in ("e0_approx", "e50_approx", "median_age", "x_H1")
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
    grid.set_axis_labels("Indicator value", "Maximum observed cumulative hazard")
    grid.set_titles("{col_name}")
    for ax in grid.axes.flat:
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", color="#dfe5eb", linewidth=0.8)
    if grid.legend is not None:
        grid.legend.set_title("Location")
        grid.legend.set_bbox_to_anchor((1.02, 0.95))
        grid.legend._loc = 2
        grid.legend.get_frame().set_facecolor("white")
        grid.legend.get_frame().set_edgecolor("#d7dbe0")
        for text in grid.legend.texts:
            text.set_text(_display_label(text.get_text()))
    grid.fig.subplots_adjust(top=0.88, right=0.82, wspace=0.25, hspace=0.32)
    grid.fig.suptitle(
        "Longevity indicators and cumulative hazard",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path)


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
    plot_data = plot_data.loc[plot_data["indicator"] != "modal_age"].copy()
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
    return _finish(fig, output_path)


def plot_regional_hazard_by_sex(
    df,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Risco acumulado nas regiões brasileiras",
):
    """Compare cumulative hazard for Brazilian regions in sex facets."""

    return _plot_curves_by_sex(
        df,
        value="H",
        regions=REGION_ORDER,
        title=title,
        ylabel=r"Risco acumulado, $H(x)$",
        output_path=output_path,
        profile=profile,
        reference=1.0,
    )


def plot_regional_survival_by_sex(
    df,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Sobrevivência nas regiões brasileiras",
):
    """Compare normalized survival for Brazilian regions in sex facets."""

    return _plot_curves_by_sex(
        df,
        value="l",
        regions=REGION_ORDER,
        title=title,
        ylabel=r"Proporção de sobreviventes, $\ell(x)$",
        output_path=output_path,
        profile=profile,
        reference=float(np.exp(-1)),
    )


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
        xlabel="Age (years)",
        ylabel="Cumulative hazard difference",
        title="Regional difference: H_North - H_Northeast",
    )
    _legend_outside(ax, title="Sex")
    return _finish(fig, output_path)


def plot_sex_hazard_gap_by_region(
    df,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Excesso de risco acumulado entre os homens",
):
    """Plot ``H_male - H_female`` by age for all Brazilian regions."""

    _require_columns(df, ("country", "year", "age", "H"), title)
    plot_data = _brazil_region_data(df)
    _validate_unique_series(plot_data, title)
    wide = plot_data.pivot(index=["region", "age"], columns="sex", values="H").reset_index()
    if not {"Female", "Male"}.issubset(wide.columns):
        raise ValueError(f"{title}: são necessários dados de mulheres e homens.")
    wide["gap"] = wide["Male"] - wide["Female"]
    wide = wide.dropna(subset=["gap"])

    fig, ax, spec = _new_subplots(profile, size="standard")
    regions = [region for region in REGION_ORDER if region in wide["region"].unique()]
    for region in regions:
        series = wide.loc[wide["region"] == region].sort_values("age")
        ax.plot(
            series["age"],
            series["gap"],
            color=REGION_COLORS[region],
            linewidth=spec.line_width,
            marker="o",
            markersize=spec.marker_size,
            markeredgecolor="white",
            markeredgewidth=0.55,
            zorder=3,
        )
    ax.axhline(0, color=ZERO, linewidth=1.1, zorder=2)
    style_axis(
        ax,
        xlabel="Idade (anos)",
        ylabel=r"Diferença $H_{homens}(x)-H_{mulheres}(x)$",
        grid_axis="y",
    )
    start_age = _analysis_start_age(spec)
    ax.set_xlim(start_age, MAX_ANALYSIS_AGE + 18)
    ax.set_xticks([40, 50, 60, 70, 80, 90] if start_age else [0, 20, 40, 60, 80, 90])
    ax.yaxis.set_major_formatter(decimal_formatter(2))
    ax.margins(y=0.12)
    _direct_line_labels(
        ax,
        wide.loc[wide["region"].isin(regions)],
        category="region",
        x="age",
        y="gap",
        colors=REGION_COLORS,
    )

    add_header(
        fig,
        title,
        _subtitle(
            plot_data,
            profile=spec,
            extra="positivo = maior risco masculino",
        ),
    )
    _finalize_layout(fig, left=0.11, right=0.94, bottom=0.16, top=0.82)
    return _finish(fig, output_path, note=_method_note(include_h=True))


def plot_benchmark_hazard_gap_vs_chile(
    df,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Diferença de risco em relação ao Chile",
):
    """Plot descriptive Brazilian regional hazard gaps against Chile, by sex."""

    _require_columns(df, ("country", "year", "age", "H"), title)
    selected = _add_region_sex(_analysis_age_data(df))
    selected = selected.loc[selected["region"].isin(ALL_REGION_ORDER)].copy()
    _validate_unique_series(selected, title)
    wide = selected.pivot(index=["sex", "age"], columns="region", values="H").reset_index()
    rows = []
    for region in REGION_ORDER:
        if region not in wide.columns or "Chile" not in wide.columns:
            continue
        temp = wide[["sex", "age", "Chile", region]].copy()
        temp["region"] = region
        temp["gap"] = temp[region] - temp["Chile"]
        rows.append(temp[["sex", "age", "region", "gap"]])
    if not rows:
        raise ValueError(f"{title}: não há pares completos entre regiões brasileiras e Chile.")
    plot_data = pd.concat(rows, ignore_index=True).dropna(subset=["gap"])
    sexes = [sex for sex in SEX_ORDER if sex in plot_data["sex"].unique()]

    fig, axes, spec = _new_subplots(
        profile,
        ncols=len(sexes),
        sharex=True,
        sharey=True,
        size="wide",
        squeeze=False,
    )
    axes = axes.ravel()
    start_age = _analysis_start_age(spec)
    for ax, sex in zip(axes, sexes):
        sex_data = plot_data.loc[plot_data["sex"] == sex]
        for region in REGION_ORDER:
            series = sex_data.loc[sex_data["region"] == region].sort_values("age")
            if series.empty:
                continue
            ax.plot(
                series["age"],
                series["gap"],
                color=REGION_COLORS[region],
                linewidth=spec.line_width,
                marker="o",
                markersize=spec.marker_size,
                markeredgecolor="white",
                markeredgewidth=0.55,
                zorder=3,
            )
        ax.axhline(0, color=ZERO, linewidth=1.1, zorder=2)
        style_axis(
            ax,
            xlabel="Idade (anos)",
            ylabel=r"Diferença $H_{Brasil}(x)-H_{Chile}(x)$" if ax is axes[0] else "",
            grid_axis="y",
        )
        ax.set_title(_display_label(sex), fontweight="semibold", pad=8)
        ax.set_xlim(start_age, MAX_ANALYSIS_AGE + 18)
        ax.set_xticks([40, 50, 60, 70, 80, 90] if start_age else [0, 20, 40, 60, 80, 90])
        ax.yaxis.set_major_formatter(decimal_formatter(2))
        ax.margins(y=0.12)
        _direct_line_labels(
            ax,
            sex_data,
            category="region",
            x="age",
            y="gap",
            colors=REGION_COLORS,
        )

    add_header(
        fig,
        title,
        _subtitle(
            selected,
            profile=spec,
            extra="positivo = maior risco no Brasil (comparação descritiva)",
        ),
    )
    _finalize_layout(fig, left=0.09, right=0.95, bottom=0.16, top=0.82, wspace=0.2)
    return _finish(
        fig,
        output_path,
        note=_method_note(include_h=True, comparison_warning=True),
    )


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
        cbar_kws={"label": "Standardized value"},
        ax=ax,
    )
    ax.set_title("Standardized indicator summary", loc="left", pad=TITLE_PAD, fontweight="semibold")
    ax.set_xlabel("Indicator")
    ax.set_ylabel("Location")
    ax.tick_params(axis="x", rotation=30)
    ax.tick_params(axis="y", rotation=0)
    return _finish(fig, output_path)


def plot_indicator_bars_brazil_regions(
    indicators,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Indicadores selecionados por região e sexo",
):
    """Compare women and men with compact dumbbells instead of redundant bars."""

    _require_columns(indicators, ("country", "year", *REPORT_INDICATORS), title)
    plot_data = _brazil_region_data(indicators)
    if plot_data.duplicated(["region", "sex"], keep=False).any():
        raise ValueError(f"{title}: filtre um único ano por região e sexo.")

    fig, axes, spec = _new_subplots(
        profile,
        nrows=2,
        ncols=3,
        sharey=True,
        size="grid",
        squeeze=False,
    )
    regions = [region for region in REGION_ORDER if region in plot_data["region"].unique()]
    y_positions = np.arange(len(regions))

    for index, (ax, indicator) in enumerate(zip(axes.flat, REPORT_INDICATORS)):
        values = plot_data.pivot(index="region", columns="sex", values=indicator).reindex(regions)
        for y, region in zip(y_positions, regions):
            female = values.loc[region, "Female"] if "Female" in values else np.nan
            male = values.loc[region, "Male"] if "Male" in values else np.nan
            if np.isfinite(female) and np.isfinite(male):
                ax.plot(
                    [female, male],
                    [y, y],
                    color="#CBD5E1",
                    linewidth=spec.line_width + 0.4,
                    solid_capstyle="round",
                    zorder=1,
                )
            for sex, value in (("Female", female), ("Male", male)):
                if not np.isfinite(value):
                    continue
                ax.scatter(
                    value,
                    y,
                    s=(spec.marker_size * 2.0) ** 2,
                    color=SEX_COLORS[sex],
                    marker=SEX_MARKERS[sex],
                    edgecolor="white",
                    linewidth=0.7,
                    zorder=3,
                )

        ax.set_title(indicator_label(indicator), loc="left", fontweight="semibold", pad=7)
        style_axis(
            ax,
            xlabel="" if indicator.startswith("H_") else "Idade (anos)",
            ylabel="",
            grid_axis="x",
        )
        ax.set_yticks(y_positions)
        if index % 3 == 0:
            ax.set_yticklabels([_display_label(region) for region in regions])
        else:
            ax.tick_params(axis="y", labelleft=False)
        ax.xaxis.set_major_formatter(decimal_formatter(2 if indicator.startswith("H_") else 1))
        ax.margins(x=0.12)

    axes.flat[0].invert_yaxis()

    add_header(
        fig,
        title,
        _subtitle(
            plot_data,
            profile=spec,
            extra="H menor = menor risco; idades maiores = maior sobrevivência",
        ),
    )
    _sex_legend(fig, SEX_ORDER)
    _finalize_layout(fig, left=0.15, right=0.975, bottom=0.14, top=0.70, wspace=0.32, hspace=0.48)
    return _finish(
        fig,
        output_path,
        note=_method_note(
            include_h=True,
            extra="vida média restrita calculada pela área sob ℓ(x) entre 0 e 90 anos",
        ),
    )


def plot_conditional_survival(
    conditional_survival,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Probabilidade de sobrevivência entre idades selecionadas",
):
    """Plot conditional survival as aligned dot plots, paired by sex when possible."""

    required = ("country", "year", "start_age", "end_age", "conditional_survival")
    _require_columns(conditional_survival, required, title)
    plot_data = _add_region_sex(conditional_survival).dropna(subset=["conditional_survival"])
    if plot_data.duplicated(["region", "sex", "start_age", "end_age"], keep=False).any():
        raise ValueError(f"{title}: filtre um único ano por localidade e sexo.")
    plot_data["conditional_survival_pct"] = plot_data["conditional_survival"] * 100
    transitions = (
        plot_data[["start_age", "end_age"]]
        .drop_duplicates()
        .sort_values(["start_age", "end_age"])
        .itertuples(index=False, name=None)
    )
    transitions = _order_intervals(list(transitions))
    regions = [region for region in ALL_REGION_ORDER if region in plot_data["region"].unique()]
    sexes = [sex for sex in SEX_ORDER if sex in plot_data["sex"].unique()]
    if not transitions or not regions:
        raise ValueError(f"{title}: não há observações válidas para plotar.")

    fig, axes, spec = _new_subplots(
        profile,
        ncols=len(transitions),
        sharey=True,
        size="wide",
        squeeze=False,
    )
    axes = axes.ravel()
    y_positions = np.arange(len(regions))
    for index, (ax, (start_age, end_age)) in enumerate(zip(axes, transitions)):
        subset = plot_data.loc[
            (plot_data["start_age"] == start_age) & (plot_data["end_age"] == end_age)
        ]
        values = subset.pivot(index="region", columns="sex", values="conditional_survival_pct").reindex(regions)
        if len(sexes) == 2:
            for y, region in zip(y_positions, regions):
                female = values.loc[region, "Female"] if "Female" in values else np.nan
                male = values.loc[region, "Male"] if "Male" in values else np.nan
                if np.isfinite(female) and np.isfinite(male):
                    ax.plot(
                        [female, male],
                        [y, y],
                        color="#CBD5E1",
                        linewidth=spec.line_width,
                        solid_capstyle="round",
                        zorder=1,
                    )
                for sex, value in (("Female", female), ("Male", male)):
                    if np.isfinite(value):
                        ax.scatter(
                            value,
                            y,
                            s=(spec.marker_size * 2.0) ** 2,
                            color=SEX_COLORS[sex],
                            marker=SEX_MARKERS[sex],
                            edgecolor="white",
                            linewidth=0.7,
                            zorder=3,
                        )
        else:
            sex = sexes[0] if sexes else "Male"
            for y, region in zip(y_positions, regions):
                value = values.loc[region, sex] if sex in values else np.nan
                if not np.isfinite(value):
                    continue
                ax.scatter(
                    value,
                    y,
                    s=(spec.marker_size * 2.1) ** 2,
                    color=REGION_COLORS[region],
                    marker="o",
                    edgecolor="white",
                    linewidth=0.7,
                    zorder=3,
                )
                ax.text(
                    value,
                    y - 0.18,
                    format_pt(value, 1, suffix="%"),
                    ha="center",
                    va="bottom",
                    fontsize=spec.note_size,
                    color=REGION_COLORS[region],
                )

        observed = subset["conditional_survival_pct"]
        span = max(observed.max() - observed.min(), 2.0)
        lower = max(0, np.floor((observed.min() - span * 0.25) / 5) * 5)
        upper = min(100, np.ceil((observed.max() + span * 0.25) / 5) * 5)
        if lower == upper:
            lower, upper = max(0, lower - 5), min(100, upper + 5)
        ax.set_xlim(lower, upper)
        ax.set_title(f"{int(start_age)}–{int(end_age)} anos", fontweight="semibold", pad=8)
        style_axis(ax, xlabel="Probabilidade (%)", ylabel="", grid_axis="x")
        ax.xaxis.set_major_formatter(decimal_formatter(0, suffix="%"))
        ax.set_yticks(y_positions)
        if index == 0:
            ax.set_yticklabels([_display_label(region) for region in regions])
        else:
            ax.tick_params(axis="y", labelleft=False)

    axes[0].invert_yaxis()
    add_header(
        fig,
        title,
        _subtitle(
            plot_data,
            profile=spec,
            extra="P(idade final | idade inicial)",
        ),
    )
    if len(sexes) == 2:
        _sex_legend(fig, sexes)
        top = 0.70
    else:
        top = 0.81
    _finalize_layout(fig, left=0.14, right=0.975, bottom=0.19, top=top, wspace=0.22)
    return _finish(
        fig,
        output_path,
        note=_method_note(include_h=False, comparison_warning="Chile" in regions),
    )


def plot_age_band_hazard_contributions(
    age_band_contributions,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Composição do risco acumulado por faixa etária",
):
    """Plot disjoint bands as stacks and overlapping intervals as dot panels."""

    required = ("country", "year", "start_age", "end_age", "hazard_increment")
    _require_columns(age_band_contributions, required, title)
    plot_data = _add_region_sex(age_band_contributions).dropna(subset=["hazard_increment"])
    if plot_data.duplicated(["region", "sex", "start_age", "end_age"], keep=False).any():
        raise ValueError(f"{title}: filtre um único ano por localidade e sexo.")
    intervals = _order_intervals(list(
        plot_data[["start_age", "end_age"]]
        .drop_duplicates()
        .sort_values(["start_age", "end_age"])
        .itertuples(index=False, name=None)
    ))
    disjoint = all(end <= next_start for (_, end), (next_start, _) in zip(intervals, intervals[1:]))
    regions = [region for region in ALL_REGION_ORDER if region in plot_data["region"].unique()]
    sexes = [sex for sex in SEX_ORDER if sex in plot_data["sex"].unique()]

    if disjoint:
        fig, axes, spec = _new_subplots(
            profile,
            ncols=len(sexes),
            sharex=True,
            sharey=True,
            size="wide",
            squeeze=False,
        )
        axes = axes.ravel()
        y_positions = np.arange(len(regions))
        band_colors = ["#DCEAF4", "#9CC3DC", "#4F8FBA", "#174E75", "#0B2F4A"]
        band_colors = band_colors[-len(intervals) :]
        max_total = 0.0
        for ax, sex in zip(axes, sexes):
            left = np.zeros(len(regions))
            sex_data = plot_data.loc[plot_data["sex"] == sex]
            for color, (start_age, end_age) in zip(band_colors, intervals):
                band = (
                    sex_data.loc[
                        (sex_data["start_age"] == start_age) & (sex_data["end_age"] == end_age)
                    ]
                    .set_index("region")["hazard_increment"]
                    .reindex(regions)
                    .fillna(0)
                    .to_numpy(float)
                )
                ax.barh(
                    y_positions,
                    band,
                    left=left,
                    color=color,
                    edgecolor="white",
                    linewidth=0.45,
                    height=0.66,
                    zorder=3,
                )
                left += band
            max_total = max(max_total, float(left.max(initial=0)))
            for y, total in zip(y_positions, left):
                ax.text(
                    total,
                    y,
                    f"  {format_pt(total, 2)}",
                    va="center",
                    ha="left",
                    fontsize=spec.note_size,
                    color=MUTED,
                )
            ax.set_title(_display_label(sex), fontweight="semibold", pad=8)
            style_axis(
                ax,
                xlabel=r"Risco acumulado até 90 anos, $H(90)$",
                ylabel="",
                grid_axis="x",
            )
            ax.set_yticks(y_positions)
            if ax is axes[0]:
                ax.set_yticklabels([_display_label(region) for region in regions])
            else:
                ax.tick_params(axis="y", labelleft=False)
            ax.xaxis.set_major_formatter(decimal_formatter(1))
        axes[0].invert_yaxis()
        for ax in axes:
            ax.set_xlim(0, max_total * 1.14)

        handles = [Patch(facecolor=color, edgecolor="white") for color in band_colors]
        labels = [f"{int(start)}–{int(end)}" for start, end in intervals]
        add_header(
            fig,
            title,
            _subtitle(plot_data, profile=spec, extra="faixas somam H(90)"),
        )
        _top_legend(fig, handles, labels, ncol=len(labels))
        _finalize_layout(fig, left=0.14, right=0.975, bottom=0.19, top=0.70, wspace=0.16)
        note_extra = "faixas etárias mutuamente exclusivas"
    else:
        if len(sexes) > 1:
            raise ValueError(
                f"{title}: intervalos sobrepostos devem ser filtrados para um único sexo."
            )
        fig, axes, spec = _new_subplots(
            profile,
            ncols=len(intervals),
            sharey=True,
            size="wide",
            squeeze=False,
        )
        axes = axes.ravel()
        y_positions = np.arange(len(regions))
        for index, (ax, (start_age, end_age)) in enumerate(zip(axes, intervals)):
            subset = plot_data.loc[
                (plot_data["start_age"] == start_age) & (plot_data["end_age"] == end_age)
            ].set_index("region")
            values = subset["hazard_increment"].reindex(regions)
            for y, region, value in zip(y_positions, regions, values):
                if not np.isfinite(value):
                    continue
                ax.scatter(
                    value,
                    y,
                    s=(spec.marker_size * 2.1) ** 2,
                    color=REGION_COLORS[region],
                    edgecolor="white",
                    linewidth=0.7,
                    zorder=3,
                )
                ax.text(
                    value,
                    y - 0.18,
                    format_pt(value, 3),
                    ha="center",
                    va="bottom",
                    fontsize=spec.note_size,
                    color=REGION_COLORS[region],
                )
            ax.set_title(f"{int(start_age)}–{int(end_age)} anos", fontweight="semibold", pad=8)
            style_axis(ax, xlabel=r"Incremento de $H(x)$", ylabel="", grid_axis="x")
            ax.set_xlim(0, max(float(values.max()) * 1.18, 0.01))
            ax.xaxis.set_major_formatter(decimal_formatter(2))
            ax.set_yticks(y_positions)
            if index == 0:
                ax.set_yticklabels([_display_label(region) for region in regions])
            else:
                ax.tick_params(axis="y", labelleft=False)
        axes[0].invert_yaxis()
        display_title = (
            "Incremento do risco em intervalos selecionados"
            if title == "Composição do risco acumulado por faixa etária"
            else title
        )
        add_header(
            fig,
            display_title,
            _subtitle(
                plot_data,
                profile=spec,
                extra="20–60 é o total dos intervalos 20–40 e 40–60",
            ),
        )
        _finalize_layout(fig, left=0.14, right=0.975, bottom=0.19, top=0.81, wspace=0.22)
        note_extra = "intervalos exibidos se sobrepõem e não devem ser somados novamente"

    return _finish(
        fig,
        output_path,
        note=_method_note(include_h=True, comparison_warning="Chile" in regions, extra=note_extra),
    )


def plot_sex_indicator_gaps(
    sex_gaps,
    output_path: str | Path | None = None,
    *,
    profile: str | FigureProfile = "report",
    title: str = "Diferenças entre mulheres e homens nos indicadores",
):
    """Plot female-minus-male gaps, separating risk metrics from years."""

    required = ("region", "year", "indicator", "gap_female_minus_male")
    _require_columns(sex_gaps, required, title)
    indicators = ("H_80", "H_90", "x_H1", "median_age", "e0_approx")
    plot_data = sex_gaps.loc[
        sex_gaps["indicator"].isin(indicators)
        & sex_gaps["gap_female_minus_male"].notna()
    ].copy()
    if plot_data.duplicated(["region", "indicator"], keep=False).any():
        raise ValueError(f"{title}: filtre um único ano por região.")
    regions = [region for region in ALL_REGION_ORDER if region in plot_data["region"].unique()]

    spec = set_theme(profile)
    figsize = (7.2, 7.2) if spec.name == "report" else (12.0, 7.4)
    fig = plt.figure(figsize=figsize)
    fig._figure_profile = spec
    grid = fig.add_gridspec(2, 6)
    axes = [
        fig.add_subplot(grid[0, 0:3]),
        fig.add_subplot(grid[0, 3:6]),
        fig.add_subplot(grid[1, 0:2]),
        fig.add_subplot(grid[1, 2:4]),
        fig.add_subplot(grid[1, 4:6]),
    ]
    y_positions = np.arange(len(regions))

    for index, (ax, indicator) in enumerate(zip(axes, indicators)):
        values = (
            plot_data.loc[plot_data["indicator"] == indicator]
            .set_index("region")["gap_female_minus_male"]
            .reindex(regions)
        )
        colors = [REGION_COLORS[region] for region in regions]
        ax.barh(
            y_positions,
            values,
            color=colors,
            height=0.65,
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
        ax.axvline(0, color=ZERO, linewidth=1.0, zorder=2)
        finite = values[np.isfinite(values)]
        span = max(float(finite.max() - finite.min()), float(finite.abs().max()) * 0.2, 0.01)
        for y, value in zip(y_positions, values):
            if not np.isfinite(value):
                continue
            ax.text(
                value + (span * 0.025 if value >= 0 else -span * 0.025),
                y,
                format_pt(value, 2 if indicator.startswith("H_") else 1),
                ha="left" if value >= 0 else "right",
                va="center",
                fontsize=spec.note_size,
                color=TEXT,
            )
        ax.set_title(indicator_label(indicator), loc="left", fontweight="semibold", pad=7)
        style_axis(
            ax,
            xlabel=r"Mulheres − homens em $H(x)$" if indicator.startswith("H_") else "Mulheres − homens (anos)",
            ylabel="",
            grid_axis="x",
        )
        ax.set_yticks(y_positions)
        if index in (0, 2):
            ax.set_yticklabels([_display_label(region) for region in regions])
        else:
            ax.tick_params(axis="y", labelleft=False)
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(decimal_formatter(2 if indicator.startswith("H_") else 1))
        left, right = ax.get_xlim()
        ax.set_xlim(left - span * 0.08, right + span * 0.1)

    add_header(
        fig,
        title,
        _subtitle(
            plot_data,
            profile=spec,
            extra="H negativo = menor risco feminino; anos positivos = vantagem feminina",
        ),
    )
    _finalize_layout(fig, left=0.15, right=0.975, bottom=0.15, top=0.82, wspace=0.9, hspace=0.5)
    return _finish(
        fig,
        output_path,
        note=_method_note(
            include_h=True,
            comparison_warning="Chile" in regions,
            extra="vida média restrita calculada entre 0 e 90 anos",
        ),
    )
