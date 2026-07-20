"""Visual identity and export helpers for academic figures.

The plotting functions keep their data keys in English, while every label shown
to the reader is rendered in Portuguese.  Two profiles share the same visual
identity: ``report`` for documents and ``slides`` for 16:9 presentations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap
from typing import Mapping

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import seaborn as sns


@dataclass(frozen=True)
class FigureProfile:
    """Typography and export tokens for a figure destination."""

    name: str
    figsize: tuple[float, float]
    dpi: int
    base_size: float
    title_size: float
    subtitle_size: float
    label_size: float
    tick_size: float
    legend_size: float
    note_size: float
    line_width: float
    marker_size: float


PROFILES: Mapping[str, FigureProfile] = {
    "report": FigureProfile(
        name="report",
        figsize=(7.2, 4.2),
        dpi=300,
        base_size=9.5,
        title_size=14,
        subtitle_size=9.5,
        label_size=10,
        tick_size=9,
        legend_size=8.5,
        note_size=7.5,
        line_width=2.0,
        marker_size=4.0,
    ),
    "slides": FigureProfile(
        name="slides",
        figsize=(12.0, 6.75),
        dpi=220,
        base_size=14,
        title_size=22,
        subtitle_size=13.5,
        label_size=15,
        tick_size=13,
        legend_size=12.5,
        note_size=10.5,
        line_width=3.0,
        marker_size=6.0,
    ),
}

REGION_ORDER = (
    "North Brazil",
    "Northeast Brazil",
    "Central-West Brazil",
    "Southeast Brazil",
    "South Brazil",
)
ALL_REGION_ORDER = (*REGION_ORDER, "Chile")
SEX_ORDER = ("Female", "Male")

# Okabe-Ito-inspired, color-vision-deficiency-friendly categorical palette.
REGION_COLORS = {
    "North Brazil": "#0072B2",
    "Northeast Brazil": "#E69F00",
    "Central-West Brazil": "#D55E00",
    "Southeast Brazil": "#009E73",
    "South Brazil": "#CC79A7",
    "Chile": "#3D4652",
}
SEX_COLORS = {"Female": "#7B2CBF", "Male": "#0072B2"}
SEX_MARKERS = {"Female": "o", "Male": "^"}
SEX_LINESTYLES = {"Female": "-", "Male": (0, (5, 2))}

DISPLAY_LABELS_PT = {
    "North Brazil": "Norte",
    "Northeast Brazil": "Nordeste",
    "Central-West Brazil": "Centro-Oeste",
    "Southeast Brazil": "Sudeste",
    "South Brazil": "Sul",
    "Chile": "Chile",
    "Female": "Mulheres",
    "Male": "Homens",
}

INDICATOR_LABELS_PT = {
    "H_60": r"Risco acumulado $H(60)$",
    "H_70": r"Risco acumulado $H(70)$",
    "H_80": r"Risco acumulado $H(80)$",
    "H_90": r"Risco acumulado $H(90)$",
    "x_H1": r"Idade em que $H(x)=1$",
    "median_age": "Idade mediana",
    "e0_approx": "Vida média restrita",
    "e50_approx": "Vida média restrita após 50",
}

TEXT = "#1F2937"
MUTED = "#64748B"
GRID = "#D9E1E8"
SPINE = "#CBD5E1"
ZERO = "#334155"


def get_profile(profile: str | FigureProfile = "report") -> FigureProfile:
    """Return a validated figure profile."""

    if isinstance(profile, FigureProfile):
        return profile
    try:
        return PROFILES[profile]
    except KeyError as exc:
        valid = ", ".join(PROFILES)
        raise ValueError(f"Perfil visual desconhecido: {profile!r}. Use {valid}.") from exc


def apply_theme(profile: str | FigureProfile = "report") -> FigureProfile:
    """Apply the shared academic theme and return the resolved profile."""

    spec = get_profile(profile)
    sns.set_theme(
        style="whitegrid",
        context="paper" if spec.name == "report" else "talk",
        font="DejaVu Sans",
    )
    plt.rcParams.update(
        {
            "axes.edgecolor": SPINE,
            "axes.labelcolor": TEXT,
            "axes.labelsize": spec.label_size,
            "axes.linewidth": 0.9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titlecolor": TEXT,
            "axes.titlesize": spec.subtitle_size,
            "figure.dpi": 120 if spec.name == "report" else 140,
            "figure.facecolor": "white",
            "font.size": spec.base_size,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "legend.fontsize": spec.legend_size,
            "legend.frameon": False,
            "legend.title_fontsize": spec.legend_size,
            "savefig.facecolor": "white",
            "text.color": TEXT,
            "xtick.color": MUTED,
            "xtick.labelsize": spec.tick_size,
            "ytick.color": MUTED,
            "ytick.labelsize": spec.tick_size,
        }
    )
    return spec


def display_label(value: object) -> str:
    """Translate a stored category label without modifying the data."""

    raw = str(value)
    if " - " in raw:
        region, sex = raw.rsplit(" - ", 1)
        return f"{DISPLAY_LABELS_PT.get(region, region)} — {DISPLAY_LABELS_PT.get(sex, sex)}"
    return DISPLAY_LABELS_PT.get(raw, raw)


def indicator_label(value: str) -> str:
    """Return a report-ready indicator label."""

    return INDICATOR_LABELS_PT.get(value, value.replace("_", " "))


def format_pt(value: float, decimals: int = 1, *, suffix: str = "") -> str:
    """Format a number using the Brazilian decimal separator."""

    return f"{value:.{decimals}f}".replace(".", ",") + suffix


def decimal_formatter(decimals: int = 1, *, suffix: str = "") -> FuncFormatter:
    """Return a Matplotlib formatter with decimal comma."""

    return FuncFormatter(lambda value, _position: format_pt(value, decimals, suffix=suffix))


def style_axis(ax, *, xlabel: str = "", ylabel: str = "", grid_axis: str = "y") -> None:
    """Apply restrained axes styling suitable for print and projection."""

    ax.set_xlabel(xlabel, labelpad=7)
    ax.set_ylabel(ylabel, labelpad=7)
    ax.grid(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8, zorder=0)
    ax.spines["left"].set_color(SPINE)
    ax.spines["bottom"].set_color(SPINE)
    ax.tick_params(length=0)


def add_header(fig: Figure, title: str, subtitle: str = "") -> None:
    """Add a left-aligned title and optional subtitle outside the axes."""

    spec = getattr(fig, "_figure_profile", PROFILES["report"])
    title_width = 76 if spec.name == "report" else 72
    wrapped_title = textwrap.fill(title, width=title_width)
    title_lines = wrapped_title.count("\n") + 1
    fig.text(
        0.055,
        0.965,
        wrapped_title,
        ha="left",
        va="top",
        fontsize=spec.title_size,
        fontweight="bold",
        color=TEXT,
    )
    if subtitle:
        subtitle_width = 96 if spec.name == "report" else 118
        wrapped_subtitle = textwrap.fill(subtitle, width=subtitle_width)
        subtitle_y = 0.875 - (title_lines - 1) * 0.055
        fig.text(
            0.055,
            subtitle_y,
            wrapped_subtitle,
            ha="left",
            va="top",
            fontsize=spec.subtitle_size,
            color=MUTED,
            linespacing=1.15,
        )
        fig._subtitle_lines = wrapped_subtitle.count("\n") + 1
    else:
        fig._subtitle_lines = 0


def add_footer(fig: Figure, note: str, source: str) -> None:
    """Add one methodological note and one source line."""

    if getattr(fig, "_report_footer_added", False):
        return
    spec = getattr(fig, "_figure_profile", PROFILES["report"])
    note_width = 118 if spec.name == "report" else 150
    wrapped_note = textwrap.fill(note, width=note_width)
    fig.text(
        0.055,
        0.042,
        wrapped_note,
        ha="left",
        va="bottom",
        fontsize=spec.note_size,
        color=MUTED,
        linespacing=1.12,
    )
    fig.text(0.055, 0.017, source, ha="left", va="bottom", fontsize=spec.note_size, color=MUTED)
    fig._report_footer_added = True


def finish_figure(
    fig: Figure,
    output_path: str | Path | None = None,
    *,
    note: str,
    source: str = "Fonte: elaboração própria com base nas tábuas de vida registradas no projeto.",
) -> Figure:
    """Add footer, export at a fixed canvas size and return the figure."""

    add_footer(fig, note, source)
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        spec = getattr(fig, "_figure_profile", PROFILES["report"])
        fig.savefig(path, dpi=spec.dpi, facecolor="white")
    return fig
