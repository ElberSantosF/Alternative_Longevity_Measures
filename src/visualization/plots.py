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
BRAZIL_REGIONS = ("Norte (Brasil)", "Nordeste (Brasil)")
SEX_ORDER = ("Feminino", "Masculino")
REPORT_INDICATORS = ("H_60", "H_70", "H_80", "H_90", "x_H1", "median_age", "e0_approx")


def _palette_for(data, hue: str = "country"):
    levels = list(dict.fromkeys(data[hue].dropna()))
    return {level: PALETTE[index % len(PALETTE)] for index, level in enumerate(levels)}


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


def _legend_outside(ax, *, title: str = "Localidade", ncol: int = 1):
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


def _add_bar_labels(ax, *, fmt: str = "%.1f"):
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, fontsize=8, padding=3, color="#44505e")


def _style_facet_grid(grid):
    for ax in grid.axes.flat:
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", color="#e8ebef", linewidth=0.8)
        ax.set_title(ax.get_title(), pad=TITLE_PAD, fontweight="semibold")
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
    fig, ax = plt.subplots(figsize=(11, 5.8))
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
        ax.annotate(
            f"H={level}",
            xy=(1, level),
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
        xlabel="Idade (x)",
        ylabel="Hazard acumulado H(x) = -log(l)",
        title="Hazard acumulado de mortalidade",
    )
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
        xlabel="Número de desafios acumulados (k)",
        ylabel="Idade em que H atinge k",
        title="Idade em que o hazard acumulado atinge H = k",
    )
    _legend_outside(ax)
    return _finish(fig, output_path or FIGURES_DIR / "milestone_bars.png")


def plot_survival_curves(df, output_path: str | Path | None = None):
    """Plot normalized survival curves l(x)."""
    set_theme()
    fig, ax = plt.subplots(figsize=(11, 5.8))
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
        xlabel="Idade (x)",
        ylabel="Sobrevivência normalizada l(x)",
        title="Função de sobrevivência por idade",
    )
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
        xlabel="Idade fixa",
        ylabel="H(x)",
        title="Hazard acumulado em idades fixas",
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
    reference = differences["reference_country"].iloc[0] if not differences.empty else "referencia"
    y_values = differences["difference_years"].dropna()
    if not y_values.empty:
        pad = max((y_values.max() - y_values.min()) * 0.12, 1)
        ax.set_ylim(y_values.min() - pad, y_values.max() + pad)
    _style_axis(
        ax,
        xlabel="Número de desafios acumulados (k)",
        ylabel=f"Diferença em anos vs {reference}",
        title="Diferença nas idades de marcos H=k",
    )
    _legend_outside(ax)
    return _finish(fig, output_path or FIGURES_DIR / "milestone_differences.png")


def plot_correlation_heatmap(correlations, output_path: str | Path | None = None):
    """Plot a correlation matrix for longevity indicators."""
    set_theme()
    fig, ax = plt.subplots(figsize=(9.5, 8))
    sns.heatmap(
        correlations,
        vmin=-1,
        vmax=1,
        center=0,
        cmap="vlag",
        annot=True,
        fmt=".2f",
        square=True,
        linewidths=0.8,
        linecolor="white",
        cbar_kws={"label": "correlação"},
        ax=ax,
    )
    ax.set_title("Correlação entre indicadores de longevidade", loc="left", pad=TITLE_PAD, fontweight="semibold")
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

    grid = sns.relplot(
        data=plot_data,
        x="value",
        y="H_max",
        hue="country",
        col="indicator",
        col_wrap=3,
        palette=_palette_for(plot_data),
        height=3.5,
        aspect=1.12,
        s=70,
        edgecolor="white",
        linewidth=0.8,
        facet_kws={"sharex": False, "sharey": True},
    )
    grid.set_axis_labels("Valor do indicador", "H_max")
    grid.set_titles("{col_name}")
    for ax in grid.axes.flat:
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", color="#e8ebef", linewidth=0.8)
    if grid.legend is not None:
        grid.legend.set_title("Localidade")
        grid.legend.set_bbox_to_anchor((1.02, 0.95))
        grid.legend._loc = 2
        grid.legend.get_frame().set_facecolor("white")
        grid.legend.get_frame().set_edgecolor("#d7dbe0")
    grid.fig.subplots_adjust(top=0.88, right=0.82, wspace=0.25, hspace=0.32)
    grid.fig.suptitle(
        "Indicadores convencionais vs hazard acumulado máximo",
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

    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    sns.lineplot(
        data=plot_data,
        x="indicator",
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
        xlabel="Indicador",
        ylabel="Ranking (1 = melhor)",
        title="Ranking comparativo por indicador",
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
    grid.set_axis_labels("Idade (x)", "Hazard acumulado H(x)")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    _legend_for_grid(grid, title="Regiao")
    grid.fig.subplots_adjust(top=0.82, right=0.78, wspace=0.18)
    grid.fig.suptitle(
        "Norte vs Nordeste: hazard acumulado por sexo",
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
    grid.set_axis_labels("Idade (x)", "Sobrevivencia normalizada l(x)")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    _legend_for_grid(grid, title="Regiao")
    grid.fig.subplots_adjust(top=0.82, right=0.78, wspace=0.18)
    grid.fig.suptitle(
        "Norte vs Nordeste: sobrevivencia por sexo",
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
    wide["gap"] = wide["Norte (Brasil)"] - wide["Nordeste (Brasil)"]

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
        xlabel="Idade (x)",
        ylabel="Diferença de hazard acumulado",
        title="Gap regional: H_Norte - H_Nordeste",
    )
    _legend_outside(ax, title="Sexo")
    return _finish(fig, output_path or FIGURES_DIR / "regional_hazard_gap_by_sex.png")


def plot_sex_hazard_gap_by_region(df, output_path: str | Path | None = None):
    """Plot H_male - H_female by age for North and Northeast."""
    set_theme()
    plot_data = _brazil_region_data(df)
    wide = plot_data.pivot_table(index=["region", "age"], columns="sex", values="H").reset_index()
    wide["gap"] = wide["Masculino"] - wide["Feminino"]

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
        xlabel="Idade (x)",
        ylabel="Diferença de hazard acumulado",
        title="Gap por sexo: H_masculino - H_feminino",
    )
    _legend_outside(ax, title="Regiao")
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
    grid.set_axis_labels("Idade (x)", "Diferença de hazard acumulado vs Chile")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    _legend_for_grid(grid, title="Região")
    grid.fig.subplots_adjust(top=0.82, right=0.78, wspace=0.18)
    grid.fig.suptitle(
        "Benchmark externo: regiões brasileiras vs Chile",
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

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    sns.heatmap(
        standardized,
        cmap="vlag",
        center=0,
        linewidths=0.8,
        linecolor="white",
        annot=values,
        fmt=".1f",
        cbar_kws={"label": "valor padronizado"},
        ax=ax,
    )
    ax.set_title("Resumo padronizado dos indicadores", loc="left", pad=TITLE_PAD, fontweight="semibold")
    ax.set_xlabel("Indicador")
    ax.set_ylabel("Localidade")
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

    grid = sns.catplot(
        data=long,
        x="value",
        y="country",
        hue="sex",
        col="indicator",
        col_wrap=3,
        kind="bar",
        palette=_palette_for(long, "sex"),
        height=3.2,
        aspect=1.25,
        sharex=False,
        sharey=True,
    )
    grid.set_axis_labels("Valor", "Localidade")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    _legend_for_grid(grid, title="Sexo")
    grid.fig.subplots_adjust(top=0.88, right=0.78, wspace=0.42, hspace=0.35)
    grid.fig.suptitle(
        "Indicadores selecionados: Norte e Nordeste",
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

    grid = sns.catplot(
        data=plot_data,
        x="conditional_survival_pct",
        y="country",
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
    grid.set_axis_labels("Probabilidade condicional (%)", "Localidade")
    grid.set_titles("{col_name} anos")
    _style_facet_grid(grid)
    for ax in grid.axes.flat:
        _add_bar_labels(ax, fmt="%.1f")
    grid.fig.subplots_adjust(top=0.88, wspace=0.28, hspace=0.35)
    grid.fig.suptitle(
        "Probabilidade de sobreviver entre idades selecionadas",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "conditional_survival.png")


def plot_age_band_hazard_contributions(age_band_contributions, output_path: str | Path | None = None):
    """Plot cumulative hazard increments by age band."""
    set_theme()
    plot_data = age_band_contributions.dropna(subset=["hazard_increment"]).copy()

    grid = sns.catplot(
        data=plot_data,
        x="age_band",
        y="hazard_increment",
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
    grid.set_axis_labels("Faixa etária", "Incremento de H")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    for ax in grid.axes.flat:
        ax.tick_params(axis="x", rotation=25)
        _add_bar_labels(ax, fmt="%.2f")
    grid.fig.subplots_adjust(top=0.88, wspace=0.28, hspace=0.42)
    grid.fig.suptitle(
        "Contribuição de faixas etárias ao hazard acumulado",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "age_band_hazard_contributions.png")


def plot_sex_indicator_gaps(sex_gaps, output_path: str | Path | None = None):
    """Plot female-minus-male gaps for selected indicators."""
    set_theme()
    plot_data = sex_gaps.dropna(subset=["gap_female_minus_male"]).copy()

    grid = sns.catplot(
        data=plot_data,
        x="gap_female_minus_male",
        y="region",
        hue="region",
        col="indicator",
        col_wrap=3,
        kind="bar",
        palette=_palette_for(plot_data, "region"),
        height=3.2,
        aspect=1.25,
        sharex=False,
        sharey=True,
        legend=False,
    )
    grid.set_axis_labels("Feminino - Masculino", "Localidade")
    grid.set_titles("{col_name}")
    _style_facet_grid(grid)
    for ax in grid.axes.flat:
        ax.axvline(0, color="#28323f", linewidth=1)
        _add_bar_labels(ax, fmt="%.2f")
    grid.fig.subplots_adjust(top=0.88, wspace=0.42, hspace=0.35)
    grid.fig.suptitle(
        "Gap feminino-masculino nos indicadores de longevidade",
        x=0.04,
        ha="left",
        fontweight="semibold",
    )
    return _finish(grid.fig, output_path or FIGURES_DIR / "sex_indicator_gaps.png")
