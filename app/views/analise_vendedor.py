import streamlit as st
import pandas as pd
from layout.cards import IndicadoresResumo
from layout.charts import ChartBuilder
from data.processor import Agrupador
from layout.rankings import Rankings

def run(df: pd.DataFrame):
    st.subheader("🧑‍💼 Análise por Vendedor")
    st.markdown("Visualize o desempenho de cada vendedor em termos de faturamento, volume e preços praticados.")

    # Filtro de datas
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()
    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)

    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Aplicação dos filtros
    processor = Agrupador(df)
    filtros = st.session_state.get("filtros", {})
    df_filtrado = processor.filtrar(filtros)

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")
        return

    # Indicadores principais
    resumo = IndicadoresResumo(df_filtrado)
    resumo.exibir()

    # Gráficos
    charts = ChartBuilder(df_filtrado)
    charts.plot_preco_unitario()
    charts.plot_volume()

    # Evolução por vendedor
    st.subheader("📈 Evolução Mensal por Vendedor")

    df_vendedor = df_filtrado.groupby(["VENDEDOR", "ANO_MES"]).agg({
        "VL.BRUTO": "sum",
        "QTDE": "sum",
        "PRECO_UNIT": "mean"
    }).reset_index()

    import plotly.express as px
    fig = px.line(
        df_vendedor,
        x="ANO_MES",
        y="VL.BRUTO",
        color="VENDEDOR",
        markers=True,
        labels={"VL.BRUTO": "Faturamento", "ANO_MES": "Mês"},
        title="💰 Evolução do Faturamento por Vendedor"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Ranking dos vendedores
    st.subheader("🏆 Ranking de Faturamento por Vendedor")
    rankings = Rankings(df_filtrado)
    rankings.exibir()
