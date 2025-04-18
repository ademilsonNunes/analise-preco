import streamlit as st
import pandas as pd
from layout.cards import IndicadoresResumo
from layout.charts import ChartBuilder
from data.processor import Agrupador
from layout.rankings import Rankings

def run(df: pd.DataFrame):
    st.subheader("📦 Análise Detalhada por Produto")

    # Filtro de datas com base na coluna EMISSAO
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()

    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)

    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Aplica filtros do session_state
    filtros = st.session_state.get("filtros", {})
    processor = Agrupador(df)
    df_filtrado = processor.filtrar(filtros)

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")
        return

    # Indicadores
    resumo = IndicadoresResumo(df_filtrado)
    resumo.exibir()

    # Gráficos principais
    charts = ChartBuilder(df_filtrado)
    charts.plot_preco_unitario()
    charts.plot_volume()

    # Evolução mensal por produto
    st.subheader("📊 Evolução de Preço Unitário por Produto ao Longo do Tempo")
    
    evolucao = df_filtrado.groupby(["ANO_MES", "COD.PRD", "DESC"]).agg({
        "PRECO_UNIT": "mean",
        "VL.BRUTO": "sum",
        "QTDE": "sum"
    }).reset_index()
    
    for _, grupo in evolucao.groupby(["COD.PRD", "DESC"]):
        sku = grupo["COD.PRD"].iloc[0]
        desc = grupo["DESC"].iloc[0]
    
        st.markdown(f"#### 🔹 Produto: `{sku} - {desc}`")
    
        col1, col2 = st.columns(2)
    
        with col1:
            st.line_chart(grupo.set_index("ANO_MES")["PRECO_UNIT"], height=200, use_container_width=True)
    
        with col2:
            st.bar_chart(grupo.set_index("ANO_MES")["QTDE"], height=200, use_container_width=True)
    
    # Ranking específico de produtos
    st.subheader("🏆 Produtos com Maior Crescimento de Preço (Média Mensal)")

    ranking_preco = (
        df_filtrado.groupby(["COD.PRD", "ANO_MES"])["PRECO_UNIT"]
        .mean()
        .groupby("COD.PRD")
        .pct_change()
        .groupby(df_filtrado["COD.PRD"])
        .mean()
        .dropna()
        .sort_values(ascending=False)
        .head(10)
    )

    ranking_df = ranking_preco.reset_index()
    ranking_df.columns = ["COD.PRD", "Crescimento Médio (%)"]
    ranking_df["Crescimento Médio (%)"] *= 100

    st.dataframe(ranking_df.style.format({"Crescimento Médio (%)": "{:.2f}"}))

    # Tabela detalhada
    st.subheader("📄 Detalhamento do Produto")
    processor.exibir_tabela(df_filtrado)
