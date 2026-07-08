# Longevity Project

Python project for analyzing local life table spreadsheets. The analysis uses cumulative hazard `H = -log(l)` to study exceptional survival patterns.

## Structure

```text
src/
  data/loaders.py          # Local Excel/CSV loading
  analysis/hazard.py       # l and H calculations
  analysis/milestones.py   # x_at_Hk interpolation
  analysis/indicators.py   # Comparative indicators
  visualization/plots.py   # Matplotlib/Seaborn charts
notebooks/
  01_local_excel_analysis.ipynb
data/raw/
outputs/figures/
tests/
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Data

Place the spreadsheets in `data/raw/`. The loader accepts `.xlsx`, `.xls`, and `.csv` files with age and survivor columns, using names such as `age` and `lx`.

Register the spreadsheets in `data/metadata.csv` using standardized names without accents or spaces:

```text
female_life_table_northeast_brazil_2025.xlsx
female_life_table_chile_2023.xlsx
male_life_table_northeast_brazil_2025.xlsx
male_life_table_chile_2023.xlsx
```

Example `metadata.csv`:

```csv
filename,country,year,sex,label
female_life_table_northeast_brazil_2025.xlsx,Northeast Brazil,2025,Female,Northeast Brazil - Female
```

## Analyses

The project uses period life tables only. Starting from `lx`, it calculates:

```text
l = lx / l0
H = -log(l)
H(60), H(70), H(80), H(90)
x_H1 ... x_H8
approximate median age
approximate modal age
approximate e0/e50 from the area under l(x), capped at age 90
correlations and rankings across indicators
```

Life expectancy, median age, and modal age measures are approximations derived from the `l(x)` curve because the local spreadsheets do not include `ex`, `dx`, or `ax`.
All project analyses exclude ages above 90.

## Usage

```python
from src.data.loaders import load_life_table
from src.analysis.hazard import add_survival_hazard
from src.analysis.indicators import build_indicators

df = load_life_table(
    "female_life_table_northeast_brazil_2025.xlsx",
    country="Northeast Brazil",
    year=2025,
)
lt = add_survival_hazard(df)
indicators = build_indicators(lt)
```

The main notebook generates indicators and saves charts to `outputs/figures/`.

## Tests

```bash
python -m pytest
```

## Git

Suggested workflow:

```bash
git checkout main
git checkout -b development
git add .
git commit -m "feat: scaffold longevity analysis package"
```

Use semantic commits such as `feat:`, `fix:`, `docs:`, and `refactor:`.
