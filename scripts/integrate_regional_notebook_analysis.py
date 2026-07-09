"""Integrate expanded regional analyses into the local notebook."""

from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK_PATH = Path("notebooks/01_local_excel_analysis.ipynb")


def source_text(cell: dict) -> str:
    return "".join(cell.get("source", []))


def code_cell(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def markdown_cell(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def replace_cell_after_heading(cells: list[dict], heading: str, replacement: dict) -> None:
    for index, cell in enumerate(cells[:-1]):
        if cell.get("cell_type") == "markdown" and source_text(cell).strip().startswith(heading):
            cells[index + 1] = replacement
            return
    raise ValueError(f"Heading not found: {heading}")


def insert_section_once(cells: list[dict], marker: str, new_cells: list[dict], *, before_heading: str) -> None:
    if any(marker in source_text(cell) for cell in cells):
        return
    for index, cell in enumerate(cells):
        if cell.get("cell_type") == "markdown" and source_text(cell).strip().startswith(before_heading):
            cells[index:index] = new_cells
            return
    cells.extend(new_cells)


def main() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    cells = notebook["cells"]

    for index, cell in enumerate(cells):
        cell.setdefault("id", f"regional-analysis-{index:02d}")
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

    import_source = source_text(cells[1])
    additions = [
        "    plot_indicator_bars_brazil_regions,\n",
        "    plot_regional_hazard_by_sex,\n",
        "    plot_regional_survival_by_sex,\n",
    ]
    if "plot_regional_hazard_by_sex" not in import_source:
        insert_at = import_source.index("    plot_sex_hazard_gap_by_region,\n")
        import_source = import_source[:insert_at] + "".join(additions) + import_source[insert_at:]
        cells[1]["source"] = import_source.splitlines(keepends=True)

    replace_cell_after_heading(
        cells,
        "## Visão geral",
        code_cell(
            """plot_hazard_curves(
    life_tables,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "hazard_curves_all.png",
)
plot_survival_curves(
    life_tables,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "survival_curves_all.png",
)
"""
        ),
    )

    insert_section_once(
        cells,
        "## Regiões brasileiras por sexo",
        [
            markdown_cell(
                """## Regiões brasileiras por sexo

Comparação direta das cinco regiões brasileiras adicionadas ao catálogo, separando mulheres e homens.
"""
            ),
            code_cell(
                """plot_regional_hazard_by_sex(
    life_tables,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "brazil_regions_hazard_by_sex.png",
)
plot_regional_survival_by_sex(
    life_tables,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "brazil_regions_survival_by_sex.png",
)
"""
            ),
            markdown_cell(
                """## Indicadores regionais

Resumo visual dos indicadores sintéticos por região e sexo para apoiar a seleção dos achados do relatório.
"""
            ),
            code_cell(
                """plot_indicator_bars_brazil_regions(
    indicators,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "brazil_regions_indicator_bars.png",
)
"""
            ),
        ],
        before_heading="## Diferenças por sexo",
    )

    replace_cell_after_heading(
        cells,
        "## Diferenças por sexo",
        code_cell(
            """plot_sex_hazard_gap_by_region(
    life_tables,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "sex_hazard_gap_by_region.png",
)
"""
        ),
    )

    replace_cell_after_heading(
        cells,
        "## Chile como referência externa",
        code_cell(
            """plot_benchmark_hazard_gap_vs_chile(
    life_tables,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "brazil_regions_vs_chile_hazard_gap.png",
)
"""
        ),
    )

    for cell in cells:
        text = source_text(cell)
        if text.strip() == "plot_conditional_survival(conditional_survival);\nplot_sex_indicator_gaps(sex_gaps);":
            cell["source"] = (
                """plot_conditional_survival(
    conditional_survival,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "conditional_survival.png",
)
plot_age_band_hazard_contributions(
    age_band_contributions,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "age_band_hazard_contributions.png",
)
plot_sex_indicator_gaps(
    sex_gaps,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "sex_indicator_gaps.png",
)
"""
            ).splitlines(keepends=True)
        if text.strip() == "plot_conditional_survival(male_20_60_survival);\nplot_age_band_hazard_contributions(male_20_60_hazard);":
            cell["source"] = (
                """plot_conditional_survival(
    male_20_60_survival,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "male_20_60_conditional_survival.png",
)
plot_age_band_hazard_contributions(
    male_20_60_hazard,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "male_20_60_hazard_contributions.png",
)
"""
            ).splitlines(keepends=True)

    for index, cell in enumerate(cells):
        cell.setdefault("id", f"regional-analysis-{index:02d}")

    NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
