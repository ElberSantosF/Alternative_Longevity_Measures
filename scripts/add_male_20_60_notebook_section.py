"""Add a focused male 20-60 mortality section to the local analysis notebook."""

from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK_PATH = Path("notebooks/01_local_excel_analysis.ipynb")
SECTION_TITLE = "## Mortalidade masculina entre 20, 40 e 60 anos"


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


def main() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    if any("".join(cell.get("source", [])).startswith(SECTION_TITLE) for cell in notebook["cells"]):
        return

    notebook["cells"].extend(
        [
            markdown_cell(
                """## Mortalidade masculina entre 20, 40 e 60 anos

Esta secao foca homens e compara Brasil regional contra Chile nas probabilidades condicionais `20-40`, `40-60` e `20-60`. A tabua de vida mostra diferencas de mortalidade por idade, mas nao permite atribuir diretamente a causa violencia sem dados de obitos por causa.
"""
            ),
            code_cell(
                """male_life_tables = life_tables[life_tables["country"].str.contains("Masculino")].copy()

male_20_60_survival = conditional_survival_probabilities(
    male_life_tables,
    transitions=((20, 40), (40, 60), (20, 60)),
)
male_20_60_survival.assign(
    conditional_survival_pct=lambda data: data["conditional_survival"] * 100
).pivot_table(
    index="country",
    columns="transition",
    values="conditional_survival_pct",
).round(2)
"""
            ),
            code_cell(
                """male_20_60_hazard = age_band_hazard_contributions(
    male_life_tables,
    bands=((20, 40), (40, 60), (20, 60)),
)
male_20_60_hazard.pivot_table(
    index="country",
    columns="age_band",
    values="hazard_increment",
).round(4)
"""
            ),
            code_cell(
                """plot_conditional_survival(
    male_20_60_survival,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "male_20_60_conditional_survival.png",
)
plot_age_band_hazard_contributions(
    male_20_60_hazard,
    output_path=PROJECT_ROOT / "outputs" / "figures" / "male_20_60_hazard_contributions.png",
)
"""
            ),
        ]
    )
    NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
