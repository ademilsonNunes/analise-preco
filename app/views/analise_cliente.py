import streamlit as st
import pandas as pd
from layout.cards import IndicadoresResumo
from layout.charts import ChartBuilder
from data.processor import Agrupador
from layout.rankings import Rankings

def run(df: pd.DataFrame):
    st.subheader("👥 Análise por Cliente")

    # Filtro de datas baseado na coluna EMISSAO
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()

    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)

    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Aplicando filtros do session_state
    processor = Agrupador(df)
    filtros = st.session_state.get("filtros", {})
    df_filtrado = processor.filtrar(filtros)

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")
        return

    # Indicadores
    resumo = IndicadoresResumo(df_filtrado)
    resumo.exibir()

    # Gráficos
    charts = ChartBuilder(df_filtrado)
    charts.plot_preco_unitario()
    charts.plot_volume()

    # Tabela de preço médio por cliente/mês
    st.subheader("📈 Preço Médio por Cliente e Mês")

    tabela_cliente = df_filtrado.pivot_table(
        index='CLIENTE',
        columns='ANO_MES',
        values='PRECO_UNIT',
        aggfunc='mean'
    ).sort_index(axis=1)

    st.dataframe(
        tabela_cliente.style.format("{:.2f}")
        .background_gradient(cmap='Blues', axis=1)
        .set_caption("💡 Preço Médio por Cliente ao longo do tempo")
    )

    # Ranking dos clientes por faturamento
    st.subheader("🏅 Ranking de Clientes por Faturamento")
    rankings = Rankings(df_filtrado)
    rankings.exibir()
