# Projeto Longevidade

Projeto em Python para analisar planilhas locais de tabuas de vida. A analise usa hazard acumulado `H = -log(l)` para estudar sobrevivencia excepcional.

## Estrutura

```text
src/
  data/loaders.py          # Leitura local de Excel/CSV
  analysis/hazard.py       # Calculo de l e H
  analysis/milestones.py   # Interpolacao x_at_Hk
  analysis/indicators.py   # Indicadores comparativos
  visualization/plots.py   # Graficos Matplotlib/Seaborn
notebooks/
  01_local_excel_analysis.ipynb
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

Coloque as planilhas em `data/raw/`. O loader aceita arquivos `.xlsx`, `.xls` e `.csv` com colunas de idade e sobreviventes, usando aliases como `IDADE`, `Idade`, `Age` e `lx`.

Cadastre as planilhas em `data/metadata.csv` usando nomes padronizados, sem acento e sem espaco:

```text
tabua_vida_feminina_nordeste_2025.xlsx
tabua_vida_feminina_chile_2023.xlsx
tabua_vida_masculina_nordeste_2025.xlsx
tabua_vida_masculina_chile_2023.xlsx
```

Exemplo de `metadata.csv`:

```csv
filename,country,year,sex,label
tabua_vida_feminina_nordeste_2025.xlsx,Nordeste (Brasil),2025,Feminino,Nordeste (Brasil) - Feminino
```

## Analises

O projeto usa apenas tabuas de periodo. A partir de `lx`, calcula:

```text
l = lx / l0
H = -log(l)
H(60), H(70), H(80), H(90), H(100)
x_H1 ... x_H8
idade mediana aproximada
idade modal aproximada
e0/e50/e90 aproximados por area sob l(x)
correlacoes e rankings entre indicadores
```

As medidas de expectativa de vida, mediana e moda sao aproximacoes derivadas da curva `l(x)`, porque as planilhas locais nao trazem `ex`, `dx` e `ax`.

## Uso

```python
from src.data.loaders import load_life_table
from src.analysis.hazard import add_survival_hazard
from src.analysis.indicators import build_indicators

df = load_life_table(
    "tabua_vida_feminina_nordeste_2025.xlsx",
    country="Nordeste (Brasil)",
    year=2025,
)
lt = add_survival_hazard(df)
indicators = build_indicators(lt)
```

O notebook principal gera indicadores e salva figuras em `outputs/figures/`.

## Testes

```bash
python -m pytest
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
