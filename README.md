# Projeto Longevidade

Migracao para Python do projeto de Iniciacao Cientifica sobre medidas alternativas de longevidade. A analise usa hazard acumulado `H = -log(l)` para estudar sobrevivencia excepcional, sem baixar dados automaticamente do HMD.

## Estrutura

```text
src/
  data/loaders.py          # Leitura local de Excel/CSV
  analysis/hazard.py       # Calculo de l e H
  analysis/milestones.py   # Interpolacao x_at_Hk
  analysis/indicators.py   # Indicadores comparativos
  visualization/plots.py   # Graficos Matplotlib/Seaborn
notebooks/
  01_hmd_analysis.ipynb
  02_nordeste_chile.ipynb
data/raw/
outputs/figures/
tests/
```

## Instalacao

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Dados

Coloque as planilhas originais em `data/raw/`. O loader aceita arquivos `.xlsx`, `.xls` e `.csv` com colunas de idade e sobreviventes, usando aliases como `IDADE`, `Idade`, `Age` e `lx`.

Arquivos esperados:

```text
HMD_SWE.xlsx
HMD_DNK.xlsx
HMD_FRATNP.xlsx
HMD_CHL.xlsx
HMD_JPN.xlsx
tabua_vida_feminina_nordeste_2025.xlsx
tabua_vida_feminina_chile_2023.xlsx
```

## Uso

```python
from src.data.loaders import LifeTableRepository
from src.analysis.hazard import add_survival_hazard
from src.analysis.indicators import build_indicators

repo = LifeTableRepository()
df = repo.load("tabua_vida_feminina_nordeste_2025.xlsx", country="Nordeste (Brasil)", year=2025)
lt = add_survival_hazard(df)
indicators = build_indicators(lt)
```

Os notebooks recriam os graficos originais e salvam as figuras em `outputs/figures/`.

## Testes

```bash
pytest
```

## Git

Fluxo sugerido:

```bash
git checkout main
git checkout -b development
git add .
git commit -m "feat: scaffold longevity analysis package"
```

Use commits semanticos como `feat:`, `fix:`, `docs:` e `refactor:`.

