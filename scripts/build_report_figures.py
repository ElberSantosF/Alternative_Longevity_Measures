"""Gera as figuras do relatorio academico em reports/figures.

Este script nao altera o notebook nem as figuras de outputs/figures. Ele aplica
um estilo sobrio, com tipografia serifada, grade discreta e paleta segura para
daltonismo, adequado a um documento tecnico impresso.

Uso:
    python scripts/build_report_figures.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.hazard import add_survival_hazard
from src.analysis.indicators import (
    age_band_hazard_contributions,
    build_indicators,
    conditional_survival_probabilities,
)
from src.config.settings import K_MAX
from src.data.loaders import load_life_tables_from_metadata

FIG_DIR = PROJECT_ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

REGION_PT = {
    "North Brazil": "Norte",
    "Northeast Brazil": "Nordeste",
    "Central-West Brazil": "Centro-Oeste",
    "Southeast Brazil": "Sudeste",
    "South Brazil": "Sul",
    "Chile": "Chile",
}
REGION_ORDER = [
    "North Brazil",
    "Northeast Brazil",
    "Central-West Brazil",
    "Southeast Brazil",
    "South Brazil",
]
ALL_ORDER = REGION_ORDER + ["Chile"]
REGION_COLOR = {
    "North Brazil": "#0072B2",
    "Northeast Brazil": "#E69F00",
    "Central-West Brazil": "#D55E00",
    "Southeast Brazil": "#009E73",
    "South Brazil": "#CC79A7",
    "Chile": "#111111",
}
REGION_MARKER = {
    "North Brazil": "o",
    "Northeast Brazil": "s",
    "Central-West Brazil": "^",
    "Southeast Brazil": "D",
    "South Brazil": "v",
    "Chile": "P",
}
SEX_PT = {"Female": "Mulheres", "Male": "Homens"}

TEXT = "#1A1A1A"
MUTED = "#4D4D4D"
GRID = "#D0D0D0"


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Times New Roman", "serif"],
            "mathtext.fontset": "dejavuserif",
            "font.size": 9.0,
            "axes.titlesize": 9.5,
            "axes.labelsize": 9.0,
            "axes.titleweight": "normal",
            "axes.edgecolor": MUTED,
            "axes.labelcolor": TEXT,
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.5,
            "grid.linestyle": "-",
            "grid.alpha": 0.9,
            "legend.frameon": False,
            "legend.fontsize": 8.2,
            "lines.linewidth": 1.4,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "text.color": TEXT,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 8.2,
            "ytick.labelsize": 8.2,
            "xtick.direction": "out",
            "ytick.direction": "out",
        }
    )


def pt(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


def comma_fmt(decimals: int = 1, suffix: str = "") -> FuncFormatter:
    return FuncFormatter(lambda v, _p: pt(v, decimals) + suffix)


def split_country(label: str) -> tuple[str, str]:
    region, sex = label.rsplit(" - ", 1)
    return region, sex


def panel_tag(ax, tag: str, title: str) -> None:
    ax.set_title(f"({tag}) {title}", loc="left", pad=6, color=TEXT)


def region_legend(fig, regions=ALL_ORDER, *, ncol: int = 6, y: float = 0.0, markers: bool = False):
    handles = [
        Line2D(
            [0],
            [0],
            color=REGION_COLOR[r],
            lw=1.6,
            linestyle="--" if r == "Chile" else "-",
            marker=REGION_MARKER[r] if markers else None,
            markersize=4.0,
        )
        for r in regions
    ]
    fig.legend(
        handles,
        [REGION_PT[r] for r in regions],
        loc="lower center",
        ncol=ncol,
        bbox_to_anchor=(0.5, y),
        handlelength=2.2,
        columnspacing=1.6,
    )


def save(fig, name: str) -> None:
    path = FIG_DIR / name
    fig.savefig(path)
    plt.close(fig)
    print(f"gravado: {path.relative_to(PROJECT_ROOT)}")


# ---------------------------------------------------------------- figura 1
def fig_curvas(life_tables: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 5.6), sharex=True)
    data = life_tables.copy()
    data[["region", "sex"]] = data["country"].apply(
        lambda c: pd.Series(split_country(c))
    )

    for col, sex in enumerate(("Female", "Male")):
        for row, value in enumerate(("H", "l")):
            ax = axes[row, col]
            for region in ALL_ORDER:
                sub = data[(data["region"] == region) & (data["sex"] == sex)].sort_values("age")
                ax.plot(
                    sub["age"],
                    sub[value],
                    color=REGION_COLOR[region],
                    linestyle="--" if region == "Chile" else "-",
                    lw=1.7 if region == "Chile" else 1.3,
                )
            ax.set_xlim(0, 90)
            ax.xaxis.set_major_locator(MultipleLocator(15))
            if value == "H":
                ax.set_ylim(0, 2.0)
                ax.axhline(1.0, color=MUTED, lw=0.7, linestyle=":")
                ax.yaxis.set_major_locator(MultipleLocator(0.5))
                ax.yaxis.set_major_formatter(comma_fmt(1))
                if col == 0:
                    ax.set_ylabel(r"Risco acumulado  $H(x)=-\ln l(x)$")
            else:
                ax.set_ylim(0, 1.02)
                ax.yaxis.set_major_locator(MultipleLocator(0.25))
                ax.yaxis.set_major_formatter(comma_fmt(2))
                if col == 0:
                    ax.set_ylabel(r"Sobrevivência  $l(x)$")
                ax.set_xlabel("Idade exata $x$ (anos)")

    panel_tag(axes[0, 0], "a", "Risco acumulado, mulheres")
    panel_tag(axes[0, 1], "b", "Risco acumulado, homens")
    panel_tag(axes[1, 0], "c", "Sobrevivência, mulheres")
    panel_tag(axes[1, 1], "d", "Sobrevivência, homens")
    axes[0, 0].annotate(
        r"$H=1$",
        xy=(4, 1.0),
        xytext=(4, 1.12),
        color=MUTED,
        fontsize=7.6,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    region_legend(fig, ncol=6, y=0.0)
    save(fig, "fig01_curvas_risco_sobrevivencia.png")


# ---------------------------------------------------------------- figura 2
def fig_limiar(indicators: pd.DataFrame) -> None:
    data = indicators.copy()
    data[["region", "sex"]] = data["country"].apply(
        lambda c: pd.Series(split_country(c))
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.1))

    ax = axes[0]
    ypos = np.arange(len(ALL_ORDER))[::-1]
    for y, region in zip(ypos, ALL_ORDER):
        row_f = data[(data.region == region) & (data.sex == "Female")]["x_H1"].iloc[0]
        row_m = data[(data.region == region) & (data.sex == "Male")]["x_H1"].iloc[0]
        ax.plot([row_m, row_f], [y, y], color=GRID, lw=3.0, solid_capstyle="round", zorder=1)
        ax.scatter([row_m], [y], color=MUTED, marker="^", s=34, zorder=2)
        ax.scatter([row_f], [y], color=REGION_COLOR[region], marker="o", s=34, zorder=2)
        ax.annotate(
            pt(row_f - row_m) + " anos",
            xy=((row_m + row_f) / 2, y + 0.26),
            ha="center",
            fontsize=7.4,
            color=MUTED,
        )
    ax.set_yticks(ypos)
    ax.set_yticklabels([REGION_PT[r] for r in ALL_ORDER])
    ax.set_xlim(81, 91)
    ax.set_ylim(-0.6, 5.6)
    ax.set_xlabel(r"$x_{H=1}$ (anos)")
    ax.xaxis.set_major_formatter(comma_fmt(0))
    ax.grid(axis="y", visible=False)
    panel_tag(ax, "a", r"Idade limiar $x_{H=1}$ por sexo")

    ax = axes[1]
    for _, row in data.iterrows():
        ax.scatter(
            row["x_H1"],
            row["e0_approx"],
            color=REGION_COLOR[row["region"]],
            marker="o" if row["sex"] == "Female" else "^",
            s=38,
            zorder=3,
        )
    rho = data[["x_H1", "e0_approx"]].corr(method="spearman").iloc[0, 1]
    ax.set_xlabel(r"$x_{H=1}$ (anos)")
    ax.set_ylabel("Vida média restrita a 90 anos")
    ax.xaxis.set_major_formatter(comma_fmt(0))
    ax.yaxis.set_major_formatter(comma_fmt(0))
    ax.annotate(
        r"$\rho_{Spearman} = $" + pt(rho, 2),
        xy=(0.05, 0.9),
        xycoords="axes fraction",
        fontsize=8.0,
        color=MUTED,
    )
    ax.legend(
        handles=[
            Line2D([0], [0], marker="^", color=MUTED, lw=0, markersize=5.5, label="Homens"),
            Line2D([0], [0], marker="o", color=MUTED, lw=0, markersize=5.5, label="Mulheres"),
        ],
        loc="lower right",
        fontsize=7.8,
    )
    panel_tag(ax, "b", "Concordância com o indicador convencional")

    fig.tight_layout(rect=(0, 0.09, 1, 1))
    region_legend(fig, ncol=6, y=0.0)
    save(fig, "fig02_limiar_h1.png")


# ---------------------------------------------------------------- figura 3
def fig_equivalencia(life_tables: pd.DataFrame) -> None:
    groups = {k: v.sort_values("age") for k, v in life_tables.groupby("country")}

    def h_at(label: str, age: float) -> float:
        d = groups[label]
        return float(np.interp(age, d["age"], d["H"]))

    def age_at(label: str, hazard: float) -> float:
        d = groups[label]
        return float(np.interp(hazard, d["H"], d["age"]))

    ref_ages = np.arange(40, 81, 2.5)
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.2), sharey=True)

    ax = axes[0]
    for region in ALL_ORDER:
        gaps = [
            age_at(f"{region} - Female", h_at(f"{region} - Male", a)) - a for a in ref_ages
        ]
        ax.plot(
            ref_ages,
            gaps,
            color=REGION_COLOR[region],
            linestyle="--" if region == "Chile" else "-",
            lw=1.7 if region == "Chile" else 1.3,
        )
    panel_tag(ax, "a", "Vantagem feminina dentro da mesma região")
    ax.set_ylabel("Diferença de idade equivalente (anos)")

    ax = axes[1]
    for region in REGION_ORDER:
        for sex, style in (("Female", "-"), ("Male", (0, (4, 2)))):
            gaps = [
                age_at(f"Chile - {sex}", h_at(f"{region} - {sex}", a)) - a for a in ref_ages
            ]
            ax.plot(ref_ages, gaps, color=REGION_COLOR[region], linestyle=style, lw=1.3)
    panel_tag(ax, "b", "Atraso do Chile em relação a cada região")

    for ax in axes:
        ax.axhline(0, color=MUTED, lw=0.7)
        ax.set_xlabel("Idade de referência $x$ (anos)")
        ax.set_xlim(40, 80)
        ax.set_ylim(0, 20)
        ax.xaxis.set_major_locator(MultipleLocator(10))
        ax.yaxis.set_major_locator(MultipleLocator(5))
        ax.yaxis.set_major_formatter(comma_fmt(0))

    axes[1].legend(
        handles=[
            Line2D([0], [0], color=MUTED, lw=1.3, linestyle="-", label="Mulheres"),
            Line2D([0], [0], color=MUTED, lw=1.3, linestyle=(0, (4, 2)), label="Homens"),
        ],
        loc="upper right",
        fontsize=7.8,
    )
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    region_legend(fig, ncol=6, y=0.0)
    save(fig, "fig03_idade_equivalente.png")


# ---------------------------------------------------------------- figura 4
def fig_faixas(bands: pd.DataFrame) -> None:
    data = bands.copy()
    data[["region", "sex"]] = data["country"].apply(
        lambda c: pd.Series(split_country(c))
    )
    order = ["0-40", "40-60", "60-80", "80-90"]
    shades = ["#F0F0F0", "#C6C6C6", "#8F8F8F", "#4A4A4A"]

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.2), sharey=True)
    for ax, sex, tag in zip(axes, ("Female", "Male"), ("a", "b")):
        sub = data[data.sex == sex]
        x = np.arange(len(ALL_ORDER))
        bottom = np.zeros(len(ALL_ORDER))
        for band, color in zip(order, shades):
            values = np.array(
                [
                    sub[(sub.region == r) & (sub.age_band == band)]["hazard_increment"].iloc[0]
                    for r in ALL_ORDER
                ]
            )
            ax.bar(
                x,
                values,
                bottom=bottom,
                width=0.66,
                color=color,
                edgecolor=MUTED,
                linewidth=0.5,
                label=band.replace("-", "–") if tag == "a" else None,
            )
            bottom += values
        ax.set_xticks(x)
        ax.set_xticklabels(
            [REGION_PT[r] for r in ALL_ORDER], rotation=30, ha="right", fontsize=7.8
        )
        ax.set_ylim(0, 2.05)
        ax.yaxis.set_major_locator(MultipleLocator(0.5))
        ax.yaxis.set_major_formatter(comma_fmt(1))
        ax.grid(axis="x", visible=False)
        panel_tag(ax, tag, SEX_PT[sex])
    axes[0].set_ylabel(r"Incremento de $H$ na faixa etária")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=4,
        bbox_to_anchor=(0.5, 0.0),
        title="Faixa etária (anos)",
        title_fontsize=8.2,
    )
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    save(fig, "fig04_faixas_etarias.png")


# ---------------------------------------------------------------- figura 5
def fig_condicional(cond: pd.DataFrame) -> None:
    data = cond.copy()
    data[["region", "sex"]] = data["country"].apply(
        lambda c: pd.Series(split_country(c))
    )
    transitions = ["60-80", "80-90", "60-90"]
    labels = ["60 → 80", "80 → 90", "60 → 90"]

    fig, axes = plt.subplots(1, 3, figsize=(7.1, 2.9), sharey=True)
    for ax, transition, label, tag in zip(axes, transitions, labels, "abc"):
        sub = data[data.transition == transition]
        x = np.arange(len(ALL_ORDER))
        for offset, sex, color in ((-0.19, "Female", "#5C5C5C"), (0.19, "Male", "#BDBDBD")):
            values = [
                sub[(sub.region == r) & (sub.sex == sex)]["conditional_survival"].iloc[0] * 100
                for r in ALL_ORDER
            ]
            ax.bar(
                x + offset,
                values,
                width=0.36,
                color=color,
                edgecolor=MUTED,
                linewidth=0.5,
                label=SEX_PT[sex] if tag == "a" else None,
            )
        ax.set_xticks(x)
        ax.set_xticklabels(
            [REGION_PT[r] for r in ALL_ORDER], rotation=45, ha="right", fontsize=7.4
        )
        ax.set_ylim(0, 80)
        ax.yaxis.set_major_locator(MultipleLocator(20))
        ax.yaxis.set_major_formatter(comma_fmt(0, "%"))
        ax.grid(axis="x", visible=False)
        panel_tag(ax, tag, label)
    axes[0].set_ylabel("Sobrevivência condicional")
    handles, lab = axes[0].get_legend_handles_labels()
    fig.legend(handles, lab, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    save(fig, "fig05_sobrevivencia_condicional.png")


# ---------------------------------------------------------------- figura 6
def fig_adulto_jovem(life_tables: pd.DataFrame) -> None:
    male = life_tables[life_tables["country"].str.contains("Male")].copy()
    female = life_tables[life_tables["country"].str.contains("Female")].copy()
    bands = ((20, 40), (40, 60))

    hz_m = age_band_hazard_contributions(male, bands=bands)
    hz_f = age_band_hazard_contributions(female, bands=bands)
    hz = pd.concat([hz_m, hz_f])
    hz[["region", "sex"]] = hz["country"].apply(lambda c: pd.Series(split_country(c)))

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.1), sharey=False)

    ax = axes[0]
    x = np.arange(len(ALL_ORDER))
    bottoms = {sex: np.zeros(len(ALL_ORDER)) for sex in ("Female", "Male")}
    for band, color in (("20-40", "#BDBDBD"), ("40-60", "#5C5C5C")):
        for offset, sex in ((-0.19, "Female"), (0.19, "Male")):
            values = np.array(
                [
                    hz[(hz.region == r) & (hz.sex == sex) & (hz.age_band == band)][
                        "hazard_increment"
                    ].iloc[0]
                    for r in ALL_ORDER
                ]
            )
            ax.bar(
                x + offset,
                values,
                bottom=bottoms[sex],
                width=0.36,
                color=color,
                edgecolor=MUTED,
                linewidth=0.5,
                label=(f"{band.replace('-', '–')} anos" if sex == "Female" else None),
            )
            bottoms[sex] += values
    for i, r in enumerate(ALL_ORDER):
        ax.annotate("M", xy=(i - 0.19, 0.004), ha="center", va="bottom", fontsize=6.6, color=MUTED)
        ax.annotate("H", xy=(i + 0.19, 0.004), ha="center", va="bottom", fontsize=6.6, color="#333333")
    ax.set_xticks(x)
    ax.set_xticklabels([REGION_PT[r] for r in ALL_ORDER], rotation=30, ha="right", fontsize=7.8)
    ax.set_ylabel(r"Incremento de $H$ entre 20 e 60 anos")
    ax.set_ylim(0, 0.23)
    ax.yaxis.set_major_locator(MultipleLocator(0.05))
    ax.yaxis.set_major_formatter(comma_fmt(2))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", fontsize=7.6)
    panel_tag(ax, "a", "Risco acumulado na idade adulta")

    cs_m = conditional_survival_probabilities(male, transitions=((20, 60),))
    cs_f = conditional_survival_probabilities(female, transitions=((20, 60),))
    cs = pd.concat([cs_m, cs_f])
    cs[["region", "sex"]] = cs["country"].apply(lambda c: pd.Series(split_country(c)))

    ax = axes[1]
    ypos = np.arange(len(ALL_ORDER))[::-1]
    for y, region in zip(ypos, ALL_ORDER):
        pf = cs[(cs.region == region) & (cs.sex == "Female")]["conditional_survival"].iloc[0] * 100
        pm = cs[(cs.region == region) & (cs.sex == "Male")]["conditional_survival"].iloc[0] * 100
        ax.plot([pm, pf], [y, y], color=GRID, lw=3.0, solid_capstyle="round", zorder=1)
        ax.scatter([pm], [y], color=MUTED, marker="^", s=34, zorder=2)
        ax.scatter([pf], [y], color=REGION_COLOR[region], marker="o", s=34, zorder=2)
    ax.set_yticks(ypos)
    ax.set_yticklabels([REGION_PT[r] for r in ALL_ORDER])
    ax.set_xlim(79, 96)
    ax.set_xlabel("Sobrevivência condicional de 20 a 60 anos")
    ax.xaxis.set_major_locator(MultipleLocator(4))
    ax.xaxis.set_major_formatter(comma_fmt(0, "%"))
    ax.grid(axis="y", visible=False)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="^", color=MUTED, lw=0, markersize=5.5, label="Homens"),
            Line2D([0], [0], marker="o", color=MUTED, lw=0, markersize=5.5, label="Mulheres"),
        ],
        loc="lower left",
        fontsize=7.8,
    )
    panel_tag(ax, "b", "Chance de completar a idade ativa")

    fig.tight_layout()
    save(fig, "fig06_adulto_jovem.png")


def main() -> None:
    apply_style()
    life_tables = add_survival_hazard(load_life_tables_from_metadata())
    indicators = build_indicators(life_tables, k_max=K_MAX)
    bands = age_band_hazard_contributions(life_tables)
    cond = conditional_survival_probabilities(life_tables)

    fig_curvas(life_tables)
    fig_limiar(indicators)
    fig_equivalencia(life_tables)
    fig_faixas(bands)
    fig_condicional(cond)
    fig_adulto_jovem(life_tables)


if __name__ == "__main__":
    main()
