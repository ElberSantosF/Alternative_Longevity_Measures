"""Keep only the most interpretable charts in the local analysis notebook."""

from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK_PATH = Path("notebooks/01_local_excel_analysis.ipynb")

REMOVE_EXACT_CODE = {
    "rankings",
}

REPLACEMENTS = {
    "plot_hazard_curves(life_tables)\nplot_survival_curves(life_tables)\nplot_fixed_age_hazards(indicators)\nplot_milestone_bars(milestones)": (
        "plot_hazard_curves(life_tables)\n"
        "plot_survival_curves(life_tables)\n"
    ),
    "plot_conditional_survival(conditional_survival)\nplot_age_band_hazard_contributions(age_band_contributions)\nplot_sex_indicator_gaps(sex_gaps)\n": (
        "plot_conditional_survival(conditional_survival)\n"
        "plot_sex_indicator_gaps(sex_gaps)\n"
    ),
}

IMPORTS_TO_REMOVE = {
    "    indicator_correlations,\n",
    "    indicator_rankings,\n",
    "    milestone_differences,\n",
    "    plot_correlation_heatmap,\n",
    "    plot_fixed_age_hazards,\n",
    "    plot_indicator_bars_brazil_regions,\n",
    "    plot_indicator_heatmap_standardized,\n",
    "    plot_indicator_rankings,\n",
    "    plot_indicator_scatter,\n",
    "    plot_milestone_bars,\n",
    "    plot_milestone_differences,\n",
    "    plot_regional_hazard_by_sex,\n",
    "    plot_regional_hazard_gap_by_sex,\n",
    "    plot_regional_survival_by_sex,\n",
}


def source_text(cell: dict) -> str:
    return "".join(cell.get("source", []))


def should_remove_heading(text: str) -> bool:
    normalized = text.strip().lower()
    return (
        normalized.startswith("## correla") and "rankings" in normalized
    ) or normalized in {
        "## norte vs nordeste",
        "## resumo de indicadores",
    }


def main() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cells = notebook["cells"]
    kept = []
    skip_next = False

    for index, cell in enumerate(cells):
        text = source_text(cell)
        if skip_next:
            skip_next = False
            continue
        if cell.get("cell_type") == "markdown" and should_remove_heading(text):
            skip_next = index + 1 < len(cells) and cells[index + 1].get("cell_type") == "code"
            continue
        kept.append(cell)

    for cell in kept:
        text = source_text(cell)
        if text:
            if cell.get("cell_type") == "markdown" and text.startswith("## Analises adicionais"):
                text = (
                    "## Analises adicionais\n\n"
                    "Probabilidades condicionais, tabela de decomposicao do hazard por faixa etaria "
                    "e gap feminino-masculino em indicadores resumidos.\n"
                )
            for old, new in REPLACEMENTS.items():
                text = text.replace(old, new)
            if cell.get("cell_type") == "code" and "from src." in text:
                lines = [line for line in text.splitlines(keepends=True) if line not in IMPORTS_TO_REMOVE]
                text = "".join(lines)
            cell["source"] = text.splitlines(keepends=True)

    kept = [
        cell
        for cell in kept
        if not (cell.get("cell_type") == "code" and source_text(cell).strip() in REMOVE_EXACT_CODE)
    ]

    notebook["cells"] = kept
    NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
