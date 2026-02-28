import streamlit as st
import pandas as pd
import plotly.express as px
import os
import subprocess
import sys

st.set_page_config(page_title="Brazil Banks Benchmark", layout="wide")

def ensure_outputs():
    # Garante que outputs/final_dataset.csv exista no ambiente (Cloud ou local)
    if not os.path.exists("outputs/final_dataset.csv"):
        os.makedirs("outputs", exist_ok=True)

        # Executa o pipeline de extração
        # Usa o mesmo Python do ambiente do Streamlit
        result = subprocess.run(
            [sys.executable, "src/02_extract_metrics.py"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            st.error("Falha ao gerar o dataset automaticamente.")
            st.code(result.stdout)
            st.code(result.stderr)
            st.stop()

st.title("Brazil Banks Financial Benchmark")
page = st.sidebar.selectbox("Página", ["Benchmark", "Data Quality"])

if page == "Benchmark":
    
    st.markdown("Comparação dos 5 principais bancos brasileiros (DFP CVM)")

    # ---------- Helpers ----------
    def format_brl(x):
        if pd.isna(x):
            return "-"
        # garante float
        x = float(x)
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    ensure_outputs()
    # ---------- Load data ----------
    df = pd.read_csv("outputs/final_dataset.csv")

    # Garantir tipos numéricos no dataset (evita problemas de formatação e gráfico)
    for col in ["total_assets", "total_liabilities", "equity", "net_income", "ROE", "ROA", "operating_result_proxy", "operating_ROA"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    

    # ---------- Sidebar filters ----------
    st.sidebar.header("Filtros")

    banks = sorted(df["DENOM_CIA"].dropna().unique().tolist())
    years = sorted(df["year"].dropna().unique().tolist())

    selected_banks = st.sidebar.multiselect("Bancos", banks, default=banks)
    selected_years = st.sidebar.multiselect("Anos", years, default=years)

    metric_options = {
        "Ativo Total": "total_assets",
        "Passivo Total (derivado)": "total_liabilities",
        "Patrimônio Líquido": "equity",
        "Lucro Líquido": "net_income",
        "ROE": "ROE",
        "ROA": "ROA",
        "Resultado Operacional (proxy)": "operating_result_proxy",
        "ROA Operacional": "operating_ROA",
    }
    # Adiciona automaticamente colunas YoY no seletor
    yoy_cols = [c for c in df.columns if c.endswith("_YoY")]
    for c in sorted(yoy_cols):
        # label amigável: "total_assets_YoY" -> "Crescimento YoY - total_assets"
        metric_options[f"Crescimento YoY - {c.replace('_YoY','')}"] = c
    metric_label = st.sidebar.selectbox("Métrica", list(metric_options.keys()))
    metric_col = metric_options[metric_label]

    is_money_metric = metric_col in [
    "total_assets",
    "total_liabilities",
    "equity",
    "net_income",
    "operating_result_proxy",
]

    is_ratio_metric = (metric_col in ["ROE", "ROA", "operating_ROA"]) or (
        isinstance(metric_col, str) and metric_col.endswith("_YoY")
    )

    # ---------- Filtered numeric df (for chart/calcs) ----------
    df_f = df[
        df["DENOM_CIA"].isin(selected_banks) &
        df["year"].isin(selected_years)
    ].copy()

    # Reforçar tipos numéricos após filtro (segurança extra)
    for col in ["total_assets", "total_liabilities", "equity", "net_income", "ROE", "ROA", "operating_result_proxy", "operating_ROA"]:
        if col in df_f.columns:
            df_f[col] = pd.to_numeric(df_f[col], errors="coerce")

    # ---------- Display df (formatted for table only) ----------
    df_f_display = df_f.copy()

    # Formatar colunas monetárias na tabela
    for col in ["total_assets", "total_liabilities", "equity", "net_income", "operating_result_proxy"]:
        if col in df_f_display.columns:
            df_f_display[col] = df_f_display[col].apply(format_brl)

    # Formatar ROE/ROA como %
    for col in ["ROE", "ROA", "operating_ROA"]:
        if col in df_f_display.columns:
            df_f_display[col] = df_f_display[col].apply(lambda v: "-" if pd.isna(v) else f"{v:.2%}")

    # Formatar colunas YoY como %
    for col in [c for c in df_f_display.columns if c.endswith("_YoY")]:
        df_f_display[col] = df_f_display[col].apply(lambda v: "-" if pd.isna(v) else f"{v:.2%}")

    st.subheader("Tabela filtrada")
    st.dataframe(df_f_display.sort_values(["DENOM_CIA", "year"]), use_container_width=True)

    # ---------- Chart ----------
    st.subheader(f"Gráfico - {metric_label}")

    if not df_f.empty:
        fig = px.line(
            df_f,
            x="year",
            y=metric_col,
            color="DENOM_CIA",
            markers=True,
        )

        # Hover formatado sem alterar dados
        if is_money_metric:
            fig.update_traces(
                hovertemplate="%{fullData.name}<br>Ano=%{x}<br>Valor=%{y:,.2f}<extra></extra>"
            )
        elif is_ratio_metric:
            fig.update_traces(
                hovertemplate="%{fullData.name}<br>Ano=%{x}<br>Valor=%{y:.2%}<extra></extra>"
            )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para os filtros selecionados.")

    # ---------- Ranking ----------
    st.subheader("Ranking por Ano")

    if not df_f.empty:
        for y in sorted(df_f["year"].dropna().unique()):
            st.markdown(f"### Ano {int(y)}" if float(y).is_integer() else f"### Ano {y}")

            df_year = df_f[df_f["year"] == y].copy()
            df_year = df_year.sort_values(metric_col, ascending=False)
            df_year["Rank"] = range(1, len(df_year) + 1)

            df_year_display = df_year[["Rank", "DENOM_CIA", metric_col]].copy()

            if is_money_metric:
                df_year_display[metric_col] = df_year_display[metric_col].apply(format_brl)
            elif is_ratio_metric:
                df_year_display[metric_col] = df_year_display[metric_col].apply(
                    lambda v: "-" if pd.isna(v) else f"{v:.2%}"
                )

            st.dataframe(df_year_display, use_container_width=True)
    else:
        st.warning("Nenhum dado para ranking.")

elif page == "Data Quality":
    st.header("Data Quality")
    ensure_outputs()
    # 1) Carregar dataset final (mesma fonte do Benchmark)
    df = pd.read_csv("outputs/final_dataset.csv")

    st.subheader("Visão geral")
    st.write(f"Linhas: {df.shape[0]} | Colunas: {df.shape[1]}")

    # 2) NaNs por métrica (colunas numéricas principais)
    metric_cols = [
        "total_assets",
        "equity",
        "net_income",
        "operating_result_proxy",
        "total_liabilities",
        "ROE",
        "ROA",
        "operating_ROA",
    ]
    metric_cols = [c for c in metric_cols if c in df.columns]

    nan_counts = df[metric_cols].isna().sum().reset_index()
    nan_counts.columns = ["metric", "nan_count"]
    nan_counts = nan_counts.sort_values("nan_count", ascending=False)

    st.subheader("NaNs por métrica")
    st.dataframe(nan_counts, use_container_width=True)

    # 3) Matriz de faltantes (banco x ano) para uma métrica escolhida
    st.subheader("Faltantes por banco e ano")

    metric_q = st.selectbox("Métrica para checar faltantes", metric_cols, index=0)

    missing = df.copy()
    missing["missing"] = missing[metric_q].isna()

    missing_pivot = (
        missing.pivot_table(
            index="DENOM_CIA",
            columns="year",
            values="missing",
            aggfunc="max",
        )
        .fillna(False)
        .astype(bool)
        .reset_index()
    )

    st.caption("True = valor ausente (NaN)")
    st.dataframe(missing_pivot, use_container_width=True)

    # 4) DS_CONTA usado (mapping_usage.csv)
    st.subheader("Rastreabilidade de DS_CONTA (mapping_usage.csv)")
    try:
        df_map = pd.read_csv("outputs/mapping_usage.csv", sep=";")
        st.dataframe(df_map, use_container_width=True)
    except FileNotFoundError:
        st.warning("Arquivo outputs/mapping_usage.csv não encontrado. Rode o pipeline (src/02_extract_metrics.py).")

    # 5) Unmapped (unmapped_lines_all_years.csv)
    st.subheader("Resumo de linhas não mapeadas (unmapped_lines_all_years.csv)")
    try:
        df_unm = pd.read_csv("outputs/unmapped_lines_all_years.csv", sep=";", encoding="latin1")

        # resumo por ano e demo
        grp = (
            df_unm.groupby(["year", "demo"])
            .size()
            .reset_index(name="unmapped_count")
            .sort_values(["year", "demo"])
        )

        st.dataframe(grp, use_container_width=True)

        # opcional: filtro para inspecionar DS_CONTA mais frequentes
        st.subheader("Top DS_CONTA (unmapped) por demo")
        demo_sel = st.selectbox("Demo", sorted(df_unm["demo"].unique().tolist()))
        top_ds = (
            df_unm[df_unm["demo"] == demo_sel]
            .groupby("DS_CONTA")
            .size()
            .sort_values(ascending=False)
            .head(30)
            .reset_index(name="freq")
        )
        st.dataframe(top_ds, use_container_width=True)

    except FileNotFoundError:
        st.warning("Arquivo outputs/unmapped_lines_all_years.csv não encontrado. Rode o pipeline (src/02_extract_metrics.py).")