import pandas as pd

# ===== CONFIGURAÇÃO =====
YEAR = 2023

BANKS = [
    "ITAU UNIBANCO HOLDING S.A.",
    "BCO BRASIL S.A.",
    "BCO BRADESCO S.A.",
    "BCO SANTANDER (BRASIL) S.A.",
    "BCO BTG PACTUAL S.A."
]

BASE_PATH = f"data_raw/dfp_cia_aberta_{YEAR}"

def load_csv(filename):
    path = f"{BASE_PATH}/{filename}"
    return pd.read_csv(path, sep=";", encoding="latin1")

def filter_banks(df):
    return df[df["DENOM_CIA"].isin(BANKS)]

def filter_last_exercise(df):
    return df[df["ORDEM_EXERC"] == "ÚLTIMO"]

def main():
    # Carregar BPA e BPP
    df_bpa = load_csv(f"dfp_cia_aberta_BPA_con_{YEAR}.csv")
    df_bpp = load_csv(f"dfp_cia_aberta_BPP_con_{YEAR}.csv")

    # Filtrar bancos
    df_bpa = filter_banks(df_bpa)
    df_bpp = filter_banks(df_bpp)

    # Filtrar apenas exercício atual
    df_bpa = filter_last_exercise(df_bpa)
    df_bpp = filter_last_exercise(df_bpp)

    print("BPA filtrado:", df_bpa.shape)
    print("BPP filtrado:", df_bpp.shape)

    print("DT_REFER BPA:", sorted(df_bpa["DT_REFER"].unique()))
    print("DT_REFER BPP:", sorted(df_bpp["DT_REFER"].unique()))

if __name__ == "__main__":
    main()