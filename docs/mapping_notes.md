Mapping notes (MVP)
CSVs usados (DFP)

BPA_con: usado para Ativo Total (total_assets)

BPP_con: usado para Passivo Total (total_liabilities) e Patrimônio Líquido (equity)

Colunas-chave

DENOM_CIA: nome da companhia (para filtro inicial)

DT_REFER: data de referência (ano)

ORDEM_EXERC: distingue ÚLTIMO (ano corrente) vs PENÚLTIMO (ano anterior)

DS_CONTA: descrição da linha/conta

CD_CONTA: código da conta (preferível para mapeamento quando estável)

VL_CONTA: valor

Contas validadas para bancos (2023)

total_assets: DS_CONTA = "Ativo Total" (usar ORDEM_EXERC = "ÚLTIMO")

total_liabilities: DS_CONTA = "Passivo Total" (usar ORDEM_EXERC = "ÚLTIMO")

equity: DS_CONTA = "Patrimônio Líquido Consolidado" (usar ORDEM_EXERC = "ÚLTIMO")