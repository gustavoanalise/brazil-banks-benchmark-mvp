import pandas as pd

YEARS = [2020, 2021, 2022, 2023, 2024]

BANKS = [
    "ITAU UNIBANCO HOLDING S.A.",
    "BCO BRASIL S.A.",
    "BCO BRADESCO S.A.",
    "BCO SANTANDER (BRASIL) S.A.",
    "BCO BTG PACTUAL S.A."
]

def load_csv(year: int, filename: str) -> pd.DataFrame:
    path = f"data_raw/dfp_cia_aberta_{year}/{filename}"
    return pd.read_csv(path, sep=";", encoding="latin1")

def extract_metric(df: pd.DataFrame, ds_conta: str) -> pd.DataFrame:
    # Pega apenas o exercício atual ("ÚLTIMO") e a conta exata pelo texto.
    return df[
        (df["DS_CONTA"] == ds_conta) &
        (df["ORDEM_EXERC"] == "ÚLTIMO")
    ][["DENOM_CIA", "DT_REFER", "VL_CONTA"]].copy()

def main():
    all_data = []

    for year in YEARS:
        print(f"Processando ano {year}")

        df_bpa = load_csv(year, f"dfp_cia_aberta_BPA_con_{year}.csv")
        df_bpp = load_csv(year, f"dfp_cia_aberta_BPP_con_{year}.csv")

        # Filtrar só os 5 bancos
        df_bpa = df_bpa[df_bpa["DENOM_CIA"].isin(BANKS)]
        df_bpp = df_bpp[df_bpp["DENOM_CIA"].isin(BANKS)]
        df_dre = load_csv(year, f"dfp_cia_aberta_DRE_con_{year}.csv")
        df_dre = df_dre[df_dre["DENOM_CIA"].isin(BANKS)]

        # Extrair métricas base
        total_assets = extract_metric(df_bpa, "Ativo Total")
        equity = extract_metric(df_bpp, "Patrimônio Líquido Consolidado")
        net_income = extract_metric(df_dre, "Lucro ou Prejuízo Líquido Consolidado do Período")
        net_income["metric"] = "net_income"

        total_assets["metric"] = "total_assets"
        equity["metric"] = "equity"

        year_data = pd.concat([total_assets, equity, net_income], ignore_index=True)
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

    print("\nChecagem (primeiras 10 linhas):")
    print(pivot[["DENOM_CIA", "year", "DT_REFER", "total_assets", "equity", "total_liabilities", "net_income"]].head(10))
    print("\nTotal linhas (pivot):", pivot.shape)

if __name__ == "__main__":
    main()