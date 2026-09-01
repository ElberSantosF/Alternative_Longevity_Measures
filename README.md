# Medidas Alternativas de Longevidade

Projeto de análise de tábuas de vida de período que mede longevidade na escala do
**risco acumulado de mortalidade**, `H(x) = -ln l(x)`, em vez de apenas na escala
de idade em anos. O indicador central é a **idade limiar** `x_H1`: a idade em que
uma pessoa acumulou risco igual a 1, ou seja, o equivalente à experiência média
de mortalidade da própria coorte.

A aplicação empírica compara as cinco grandes regiões do Brasil entre si e com o
Chile, por sexo, em 2023.

**Autores:** Elber Santos e Evelyn Fragoso
**Relatório:** [reports/relatorio_medidas_alternativas_longevidade.md](reports/relatorio_medidas_alternativas_longevidade.md)
(versão autocontida, com as figuras embutidas, em [`..._compartilhavel.md`](reports/relatorio_medidas_alternativas_longevidade_compartilhavel.md))

---

## Dados

Doze tábuas de vida de período de 2023, em formato abreviado (idades 0, 1, 5 e
depois grupos quinquenais até 90 anos), separadas por sexo:

| Localidade | Fonte |
| --- | --- |
| Norte, Nordeste, Centro-Oeste, Sudeste, Sul | IBGE, *Tábuas completas de mortalidade para o Brasil: 2023* |
| Chile | fonte oficial equivalente |

A análise usa apenas a coluna `lx`, normalizada por `l0`, para manter a
comparabilidade entre arquivos de origens diferentes. **Todas as análises do
projeto excluem idades acima de 90 anos** (`MAX_ANALYSIS_AGE` em
[src/config/settings.py](src/config/settings.py)).

### Registro das planilhas

As planilhas ficam em `data/raw/` e são registradas em
[data/metadata.csv](data/metadata.csv). O carregador aceita `.xlsx`, `.xls` e
`.csv`, e reconhece as colunas de idade (`age`, `x`, `idade`) e de sobreviventes
(`lx`).

```csv
filename,country,year,sex,label
female_life_table_northeast_brazil_2023.xlsx,Northeast Brazil,2023,Female,Northeast Brazil - Female
```

Duas convenções importantes:

- A coluna **`label`** é o que vira a chave `country` no data frame carregado, e
  é ela que agrupa todas as análises. O formato `"Região - Sexo"` é um contrato:
  funções como `sex_indicator_gaps` e os gráficos regionais separam região e sexo
  fazendo `rsplit(" - ")` sobre esse rótulo.
- As colunas `country` e `sex` do CSV são descritivas; quando `label` está
  presente, ela tem precedência.

Os nomes de arquivo seguem o padrão `{sexo}_life_table_{localidade}_{ano}.xlsx`,
sem acentos nem espaços.

---

## Instalação

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Duas restrições que valem registrar, porque não são óbvias no código:

- **NumPy 2.x é obrigatório.** O cálculo de vida média restrita usa
  `np.trapezoid`, que não existe no NumPy 1.x. Não relaxe esse pin.
- **Pillow** entra apenas por causa de `scripts/build_shareable_report.py`, que
  quantiza os PNGs antes de embuti-los em base64.

Testado em Python 3.11.

---

## Como reproduzir

O projeto tem saídas visuais independentes, cada uma com o seu gerador.

| Saída | Comando | Destino |
| --- | --- | --- |
| Figuras do notebook (perfil `report`) | `python scripts/generate_report_figures.py` | `outputs/figures/` |
| Figuras de apresentação (perfil `slides`) | executar `notebooks/01_local_excel_analysis.ipynb` | `outputs/figures/slides/` |
| Figuras do relatório acadêmico (`fig01`–`fig06`) | `python scripts/build_report_figures.py` | `reports/figures/` |
| Relatório autocontido, com os PNGs em base64 | `python scripts/build_shareable_report.py` | `reports/..._compartilhavel.md` |

Atenção aos dois nomes parecidos: `generate_report_figures.py` regenera as
figuras do notebook em `outputs/`, enquanto `build_report_figures.py` gera as
figuras numeradas do documento acadêmico em `reports/`, com estilo próprio
(tipografia serifada, painéis rotulados) e sem depender de
`src/visualization/plots.py`.

O conteúdo de `outputs/figures/` é ignorado pelo Git; as figuras de
`reports/figures/` são versionadas.

---

## Estrutura

```text
src/
  config/settings.py            # caminhos, K_MAX, MAX_ANALYSIS_AGE, EPSILON
  data/loaders.py               # leitura local de Excel/CSV e do metadata.csv
  analysis/hazard.py            # l = lx/l0 e H = -log(l)
  analysis/milestones.py        # x_at_Hk por interpolação linear
  analysis/indicators.py        # indicadores comparativos e agregações
  visualization/style.py        # identidade visual: perfis, paleta, rótulos PT
  visualization/plots.py        # figuras do notebook e dos outputs
notebooks/
  01_local_excel_analysis.ipynb # análise exploratória completa
scripts/                        # geradores de figuras e do relatório
data/raw/                       # planilhas de origem
data/metadata.csv               # catálogo das planilhas
outputs/figures/                # figuras geradas (ignoradas pelo Git)
reports/                        # relatório acadêmico e suas figuras
tests/                          # 22 testes de contrato
```

Os três scripts `add_male_20_60_notebook_section.py`,
`focus_notebook_graphs.py` e `integrate_regional_notebook_analysis.py` são
migrações pontuais já aplicadas ao notebook. Ficam registradas como histórico e
não precisam ser executadas de novo.

---

## O que o código calcula

A partir de `lx`, o pipeline produz:

```text
l  = lx / l0                       normalização pelo primeiro grupo etário
H  = -log(l)                       risco acumulado
H(60), H(70), H(80), H(90)         risco em idades fixas
x_H1 ... x_H8                      idades limiares por interpolação (K_MAX = 8)
```

E os indicadores derivados, todos em [src/analysis/indicators.py](src/analysis/indicators.py):

| Função | O que devolve |
| --- | --- |
| `build_indicators` | tabela larga com risco em idades fixas, indicadores convencionais e idades limiares |
| `conventional_indicators` | `e0_approx`, `e50_approx`, idade modal e idade mediana à morte |
| `conditional_survival_probabilities` | probabilidade de chegar à idade `b` dado que chegou à idade `a`; por padrão 60→80, 60→90 e 80→90 |
| `age_band_hazard_contributions` | quanto de `H` se acumula em cada faixa etária, e a participação de cada faixa no total |
| `sex_indicator_gaps` | diferença mulheres − homens por região, indicador a indicador |
| `milestone_differences` | idades limiares comparadas contra uma localidade de referência |
| `indicator_correlations`, `indicator_rankings` | concordância e ordenação entre indicadores |

Vida média (`e0_approx`, `e50_approx`), idade mediana e idade modal são
**aproximações** obtidas da curva `l(x)` por integração trapezoidal e
interpolação, porque as planilhas locais não trazem `ex`, `dx` nem `ax`. Como o
domínio para nos 90 anos, `e0_approx` é uma vida média *restrita*, e não a
esperança de vida completa.

### Uso direto

```python
from src.data.loaders import load_life_tables_from_metadata
from src.analysis.hazard import add_survival_hazard
from src.analysis.indicators import build_indicators

raw = load_life_tables_from_metadata()      # lê tudo o que está em data/metadata.csv
life_tables = add_survival_hazard(raw)      # adiciona l0, l e H
indicators = build_indicators(life_tables)  # tabela larga por localidade e ano
```

Para uma planilha só:

```python
from src.data.loaders import load_life_table

df = load_life_table(
    "female_life_table_northeast_brazil_2023.xlsx",
    country="Northeast Brazil - Female",
    year=2023,
)
```

---

## Figuras

`src/visualization/style.py` define a identidade visual compartilhada, com dois
perfis que mudam apenas tipografia e tamanho de tela:

- **`report`** — 7,2 × 4,2 pol a 300 dpi, para o documento impresso;
- **`slides`** — 12 × 6,75 pol (16:9) a 220 dpi, para projeção.

As figuras usadas no notebook e em `generate_report_figures.py` aceitam
`output_path=` e `profile=`:

```python
from src.visualization.plots import plot_hazard_curves

plot_hazard_curves(life_tables, output_path="fig.png", profile="slides")
```

As demais funções de `plots.py` (`plot_milestone_bars`, `plot_fixed_age_hazards`,
`plot_correlation_heatmap`, `plot_indicator_scatter`, `plot_indicator_rankings`,
`plot_indicator_heatmap_standardized`, `plot_milestone_differences` e
`plot_regional_hazard_gap_by_sex`) são de apoio exploratório, aceitam apenas
`output_path=` e saem sempre no perfil `report`.

Convenção de idioma do código: **as chaves de dados permanecem em inglês**
(`country`, `age`, `lx`, `Female`, `Male`) e **todo rótulo mostrado ao leitor é
renderizado em português**, pelas traduções em `DISPLAY_LABELS_PT` e
`INDICATOR_LABELS_PT`. A paleta de regiões é derivada de Okabe-Ito, segura para
daltonismo, e cada região mantém a mesma cor em todas as figuras.

---

## Principais resultados (2023)

Do relatório, para dar contexto a quem abre o repositório pela primeira vez:

- A amplitude de `x_H1` **entre as cinco regiões brasileiras** é de apenas 0,4
  ano dentro de cada sexo — mulheres de 86,5 a 86,9, homens de 82,2 a 82,6.
- A diferença **entre sexos na mesma região** vai de 3,9 a 4,6 anos, cerca de dez
  vezes a amplitude regional, e se concentra nas idades adultas jovens.
- A distância para o **Chile**, medida contra a melhor região brasileira de cada
  sexo, é de 3,6 anos entre homens e 2,3 anos entre mulheres, e se origina antes
  dos 60 anos.
- Em idade equivalente em risco, um homem de 60 anos no Nordeste carrega o risco
  acumulado de uma mulher de 71,0 anos da mesma região.
- `x_H1` concorda com os indicadores convencionais sem se reduzir a eles:
  correlação de Spearman de 0,95 com a idade mediana à morte e 0,89 com a vida
  média restrita.

O limite de 90 anos das tábuas é a limitação principal: só `x_H1` é observável, e
as idades limiares de `x_H2` a `x_H8` ficam fora do alcance dos dados. As
diferenças entre regiões brasileiras (0,05 a 0,4 ano) são menores que o erro de
interpolação das tábuas abreviadas (cerca de 0,2 ano) e devem ser lidas com
cautela.

---

## Testes

```bash
python -m pytest
```

A suíte cobre carregamento (`test_loaders.py`), risco acumulado
(`test_hazard.py`), indicadores (`test_indicators.py`) e contratos visuais
(`test_plots.py` — cores estáveis por região, presença de legenda, nota de
rodapé e comportamento dos dois perfis).

---

## Convenções de Git

Commits semânticos: `feat:`, `fix:`, `docs:`, `refactor:`.

```bash
git checkout -b development
git add .
git commit -m "feat: adiciona indicador de idade equivalente"
```
