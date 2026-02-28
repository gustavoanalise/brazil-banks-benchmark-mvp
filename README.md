# Brazil Banks Financial Benchmark (DFP via CVM)

Pipeline automatizado para extração, padronização e análise comparativa de dados financeiros dos 5 maiores bancos brasileiros utilizando DFP da CVM.

Projeto desenvolvido como MVP estruturado com foco em:

- Engenharia de dados financeiros
- Padronização multi-year
- Métricas derivadas
- Dashboard interativo em Streamlit
- Boas práticas de versionamento e rastreabilidade

---

## Objetivo

Construir um pipeline automatizado que:

1. Baixa DFP da CVM via HTTP  
2. Extrai métricas financeiras consolidadas  
3. Padroniza dataset multi-year  
4. Calcula indicadores derivados  
5. Disponibiliza dashboard interativo  

---

## Bancos analisados

Filtrados via `DENOM_CIA`:

- BCO BRASIL S.A.
- BCO BRADESCO S.A.
- BCO SANTANDER (BRASIL) S.A.
- BCO BTG PACTUAL S.A.
- ITAU UNIBANCO HOLDING S.A.

---

## Período analisado

**2020 – 2024**

---

## Métricas Implementadas

### Métricas Base

| Métrica                     | Origem  |
|-----------------------------|---------|
| total_assets                | BPA_con |
| equity                      | BPP_con |
| net_income                  | DRE_con |
| operating_result_proxy      | DRE_con |

`operating_result_proxy` é baseado em:

- Resultado Bruto de Intermediação Financeira

---

### Métricas Derivadas

- `total_liabilities = total_assets - equity`
- `ROE = net_income / equity`
- `ROA = net_income / total_assets`
- `operating_ROA = operating_result_proxy / total_assets`

---

## Arquitetura do Projeto
brazil-banks-benchmark-mvp/
│
├── data_raw/
│ └── dfp_cia_aberta_{year}/
│
├── outputs/
│ ├── final_dataset.csv
│ ├── final_dataset.xlsx
│ ├── mapping_usage.csv
│ └── unmapped_lines_all_years.csv
│
├── src/
│ ├── 02_extract_metrics.py
│ ├── 03_dre_discovery.py
│ └── app.py
│
├── requirements.txt
└── README.md

---

## Robustez e Diagnóstico

O projeto implementa:

- DS_CONTA mapping via dicionário
- Log de rastreabilidade (`mapping_usage.csv`)
- Relatório de linhas não mapeadas (`unmapped_lines_all_years.csv`)
- Pivot padronizado multi-year
- Separação entre dados brutos e outputs gerados

---

## Como Rodar o Projeto

### Criar ambiente virtual
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python src/02_extract_metrics.py
streamlit run src/app.py
```
## Dashboard

### Funcionalidades

- Filtros por banco
- Filtros por ano
- Seletor de métrica
- Ranking automático por ano
- Gráfico de evolução temporal
- Formatação monetária em R$
- Percentuais formatados corretamente

---

## Engenharia de Dados Aplicada

Este projeto demonstra:

- ETL via HTTP
- Normalização de demonstrações financeiras
- Tratamento de variações de nomenclatura (DS_CONTA)
- Métricas derivadas padronizadas
- Pipeline determinístico e reprodutível
- Organização orientada a portfólio técnico

---

## Próximos Passos Planejados

- Crescimento YoY automático
- ROE com equity médio
- Página de Data Quality no dashboard
- Deploy no Streamlit Cloud
- Containerização via Docker

---

## Fonte dos Dados

Comissão de Valores Mobiliários (CVM)

https://dados.cvm.gov.br/

---

## Autor

Gustavo Ferreira  
Senior Consultant – Financial Advisory  
Data & Financial Analytics
