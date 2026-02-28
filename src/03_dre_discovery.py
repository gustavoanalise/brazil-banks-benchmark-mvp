import pandas as pd

PATTERNS = [
    "resultado operacional",
    "resultado antes",
    "resultado bruto",
    "intermedia",
    "margem",
    "lucro operacional",
    "receita",
    "despesa",
]

def main():
    df = pd.read_csv("outputs/unmapped_lines_all_years.csv", sep=";", encoding="latin1")

    df = df[df["demo"] == "DRE"].copy()
    df["ds_lower"] = df["DS_CONTA"].astype(str).str.lower()

    mask = False
    for p in PATTERNS:
        mask = mask | df["ds_lower"].str.contains(p, na=False)

    hits = df[mask].copy()

    print("\nTotal DRE unmapped:", len(df))
    print("Total hits por padrão:", len(hits))

    # Top DS_CONTA por frequência (geral)
    top = (
        hits.groupby("DS_CONTA")
        .size()
        .sort_values(ascending=False)
        .head(40)
        .reset_index(name="freq")
    )

    print("\nTop DS_CONTA candidatos (freq):")
    print(top.to_string(index=False))

    # Opcional: salvar para você olhar com calma
    top.to_csv("outputs/dre_operating_candidates_top.csv", index=False, sep=";", encoding="latin1")
    hits.to_csv("outputs/dre_operating_candidates_lines.csv", index=False, sep=";", encoding="latin1")
    print("\nArquivos salvos em outputs/:")
    print(" - dre_operating_candidates_top.csv")
    print(" - dre_operating_candidates_lines.csv")

if __name__ == "__main__":
    main()