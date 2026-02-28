import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Brazil Banks Benchmark", layout="wide")

st.title("Brazil Banks Financial Benchmark")
st.markdown("Comparação dos 5 principais bancos brasileiros (DFP CVM)")

# ---------- Helpers ----------
def format_brl(x):
    if pd.isna(x):
        return "-"
    # garante float
    x = float(x)
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
metric_label = st.sidebar.selectbox("Métrica", list(metric_options.keys()))
metric_col = metric_options[metric_label]

is_money_metric = metric_col in ["total_assets", "total_liabilities", "equity", "net_income", "operating_result_proxy"]
is_ratio_metric = metric_col in ["ROE", "ROA", "operating_ROA"]

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