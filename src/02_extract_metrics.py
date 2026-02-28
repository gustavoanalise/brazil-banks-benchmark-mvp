import pandas as pd
import os
import zipfile
import requests

YEARS = [2020, 2021, 2022, 2023, 2024]

BANKS = [
    "ITAU UNIBANCO HOLDING S.A.",
    "BCO BRASIL S.A.",
    "BCO BRADESCO S.A.",
    "BCO SANTANDER (BRASIL) S.A.",
    "BCO BTG PACTUAL S.A."
]

DS_CONTA_MAP = {
    "total_assets": [
        "Ativo Total",
    ],
    "equity": [
        "Patrimônio Líquido Consolidado",
        # opcional (dependendo de ano/companhia, pode existir variação):
        "Patrimônio Líquido",
    ],
    "net_income": [
        "Lucro ou Prejuízo Líquido Consolidado do Período",
        # opcionais comuns em variações:
        "Lucro/Prejuízo do Período",
        "Lucro (Prejuízo) Líquido do Período",
    ],
        "operating_result_proxy": [
        "Resultado Bruto de Intermediação Financeira",
        "Resultado Bruto Intermediação Financeira",
    ],
}

DS_CONTA_BY_DEMO = {
    "BPA": DS_CONTA_MAP["total_assets"],
    "BPP": DS_CONTA_MAP["equity"],
    "DRE": DS_CONTA_MAP["net_income"] + DS_CONTA_MAP["operating_result_proxy"],
}

def build_unmapped_report(df, demo_label, year, used_ds_conta_list):
    """
    Retorna linhas (dos BANKS, ÚLTIMO) cujo DS_CONTA NÃO está em used_ds_conta_list.
    Mantém colunas essenciais para análise.
    """
    df_u = df.copy()

    # filtros padrão do projeto
    df_u = df_u[df_u["DENOM_CIA"].isin(BANKS)]
    if "ORDEM_EXERC" in df_u.columns:
        df_u = df_u[df_u["ORDEM_EXERC"] == "ÚLTIMO"]

    # exclui linhas mapeadas
    df_u = df_u[~df_u["DS_CONTA"].isin(used_ds_conta_list)]

    # seleciona colunas úteis (só as que existirem)
    cols_pref = ["DENOM_CIA", "DT_REFER", "DS_CONTA", "CD_CONTA", "VL_CONTA", "GRUPO_DFP", "ESCALA_MOEDA", "MOEDA"]
    cols = [c for c in cols_pref if c in df_u.columns]

    df_u = df_u[cols].copy()
    df_u.insert(0, "demo", demo_label)
    df_u.insert(0, "year", year)

    return df_u

def ensure_raw_data(year):
    """
    Garante que o ZIP do ano foi baixado e extraído em data_raw/dfp_cia_aberta_{year}/
    """
    folder = f"data_raw/dfp_cia_aberta_{year}"
    os.makedirs(folder, exist_ok=True)

    # Se os CSVs principais já existem, não faz nada
    expected = [
        f"{folder}/dfp_cia_aberta_BPA_con_{year}.csv",
        f"{folder}/dfp_cia_aberta_BPP_con_{year}.csv",
        f"{folder}/dfp_cia_aberta_DRE_con_{year}.csv",
    ]
    if all(os.path.exists(p) for p in expected):
        return

    url = f"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip"
    zip_path = f"{folder}/dfp_cia_aberta_{year}.zip"

    # Baixa ZIP se não existir
    if not os.path.exists(zip_path):
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    # Extrai
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(folder)

def load_csv(year: int, filename: str) -> pd.DataFrame:
    path = f"data_raw/dfp_cia_aberta_{year}/{filename}"
    return pd.read_csv(path, sep=";", encoding="latin1")

def extract_metric(df: pd.DataFrame, ds_conta: str) -> pd.DataFrame:
    # Pega apenas o exercício atual ("ÚLTIMO") e a conta exata pelo texto.
    return df[
        (df["DS_CONTA"] == ds_conta) &
        (df["ORDEM_EXERC"] == "ÚLTIMO")
    ][["DENOM_CIA", "DT_REFER", "VL_CONTA"]].copy()

def extract_metric_mapped(df, metric_name, ds_conta_candidates):
    """
    Tenta extrair uma métrica usando uma lista de possíveis DS_CONTA.
    Retorna o primeiro resultado não vazio.
    Anexa o DS_CONTA escolhido em tmp.attrs["ds_conta_used"] para rastreabilidade.
    """
    last_empty = None

    for ds in ds_conta_candidates:
        tmp = extract_metric(df, ds)
        if tmp is not None and not tmp.empty:
            tmp["metric"] = metric_name
            tmp.attrs["ds_conta_used"] = ds
            return tmp
        last_empty = tmp

    if last_empty is None:
        empty = df.head(0).assign(metric=metric_name)[["DENOM_CIA", "DT_REFER", "VL_CONTA", "metric"]]
        empty.attrs["ds_conta_used"] = None
        return empty

    last_empty["metric"] = metric_name
    last_empty.attrs["ds_conta_used"] = None
    return last_empty

def main():
    all_data = []
    mapping_usage = []
    unmapped_all = []
    for year in YEARS:
        print(f"Processando ano {year}")
        ensure_raw_data(year)

        df_bpa = load_csv(year, f"dfp_cia_aberta_BPA_con_{year}.csv")
        df_bpp = load_csv(year, f"dfp_cia_aberta_BPP_con_{year}.csv")

        # Filtrar só os 5 bancos
        df_bpa = df_bpa[df_bpa["DENOM_CIA"].isin(BANKS)]
        df_bpp = df_bpp[df_bpp["DENOM_CIA"].isin(BANKS)]
        df_dre = load_csv(year, f"dfp_cia_aberta_DRE_con_{year}.csv")
        df_dre = df_dre[df_dre["DENOM_CIA"].isin(BANKS)]

        # Unmapped reports (diagnóstico)
        unmapped_bpa = build_unmapped_report(df_bpa, "BPA", year, DS_CONTA_BY_DEMO["BPA"])
        unmapped_bpp = build_unmapped_report(df_bpp, "BPP", year, DS_CONTA_BY_DEMO["BPP"])
        unmapped_dre = build_unmapped_report(df_dre, "DRE", year, DS_CONTA_BY_DEMO["DRE"])

        unmapped_bpa.to_csv(f"outputs/unmapped_lines_{year}_BPA.csv", index=False, sep=";", encoding="latin1")
        unmapped_bpp.to_csv(f"outputs/unmapped_lines_{year}_BPP.csv", index=False, sep=";", encoding="latin1")
        unmapped_dre.to_csv(f"outputs/unmapped_lines_{year}_DRE.csv", index=False, sep=";", encoding="latin1")

        # Extrair métricas base
        total_assets = extract_metric_mapped(df_bpa, "total_assets", DS_CONTA_MAP["total_assets"])
        equity = extract_metric_mapped(df_bpp, "equity", DS_CONTA_MAP["equity"])
        net_income = extract_metric_mapped(df_dre, "net_income", DS_CONTA_MAP["net_income"])
        operating_result_proxy = extract_metric_mapped(
            df_dre,
            "operating_result_proxy",
            DS_CONTA_MAP["operating_result_proxy"]
        )

        net_income["metric"] = "net_income"
        mapping_usage.append({"year": year, "metric": "total_assets", "ds_conta_used": total_assets.attrs.get("ds_conta_used")})
        mapping_usage.append({"year": year, "metric": "equity", "ds_conta_used": equity.attrs.get("ds_conta_used")})
        mapping_usage.append({"year": year, "metric": "net_income", "ds_conta_used": net_income.attrs.get("ds_conta_used")})   
        mapping_usage.append({"year": year, "metric": "operating_result_proxy", "ds_conta_used": operating_result_proxy.attrs.get("ds_conta_used")})

        total_assets["metric"] = "total_assets"
        equity["metric"] = "equity"

        year_data = pd.concat([total_assets, equity, net_income, operating_result_proxy], ignore_index=True)
        year_data["year"] = year

        all_data.append(year_data)

    final_df = pd.concat(all_data, ignore_index=True)

    # Pivot para ter assets e equity na mesma linha por banco/ano
    pivot = final_df.pivot_table(
        index=["DENOM_CIA", "year", "DT_REFER"],
        columns="metric",
        values="VL_CONTA",
        aggfunc="first"
    ).reset_index()

    # Derivar passivo: liabilities = assets - equity
    pivot["total_liabilities"] = pivot["total_assets"] - pivot["equity"]

    # Métricas derivadas
    pivot["ROE"] = pivot["net_income"] / pivot["equity"]
    pivot["ROA"] = pivot["net_income"] / pivot["total_assets"]
    pivot["operating_ROA"] = pivot["operating_result_proxy"] / pivot["total_assets"]

    # ---------------------------
    # YoY Growth (Year over Year)
    # ---------------------------

    yoy_metrics = [
        "total_assets",
        "equity",
        "net_income",
        "operating_result_proxy",
    ]

    for metric in yoy_metrics:
        if metric in pivot.columns:
            pivot = pivot.sort_values(["DENOM_CIA", "year"])
            pivot[f"{metric}_YoY"] = (
                pivot.groupby("DENOM_CIA")[metric]
                .pct_change(fill_method=None)
            )

    # Salvar dataset final
    pivot.to_csv("outputs/final_dataset.csv", index=False)
    pivot.to_excel("outputs/final_dataset.xlsx", index=False)
    print(f"Unmapped {year} | BPA: {len(unmapped_bpa)} | BPP: {len(unmapped_bpp)} | DRE: {len(unmapped_dre)}")

    unmapped_all.append(unmapped_bpa)
    unmapped_all.append(unmapped_bpp)
    unmapped_all.append(unmapped_dre)

    df_unmapped_all = pd.concat(unmapped_all, ignore_index=True)
    df_unmapped_all.to_csv("outputs/unmapped_lines_all_years.csv", index=False, sep=";", encoding="latin1")

    print("\nArquivo salvo: outputs/unmapped_lines_all_years.csv")
    print("Total linhas unmapped (all years):", len(df_unmapped_all))

    print("\nArquivos salvos em outputs/:")
    print(" - final_dataset.csv")
    print(" - final_dataset.xlsx")

    print("\nColunas do pivot:")
    print(list(pivot.columns))

    print("\nChecagem (incluindo operating_result_proxy):")
    print(
        pivot[
            ["DENOM_CIA", "year", "total_assets", "equity", "net_income", "operating_result_proxy", "total_liabilities", "ROE", "ROA"]
        ].head(10)
    )

    print("\nNaNs em operating_result_proxy:", pivot["operating_result_proxy"].isna().sum())

    print("\nTotal linhas (pivot):", pivot.shape)

    df_mapping = pd.DataFrame(mapping_usage)
    df_mapping.to_csv("outputs/mapping_usage.csv", index=False, sep=";")

    print("\nMapping usage (DS_CONTA por ano/métrica):")
    print(df_mapping)
    print("\nArquivo salvo: outputs/mapping_usage.csv")

if __name__ == "__main__":
    main()