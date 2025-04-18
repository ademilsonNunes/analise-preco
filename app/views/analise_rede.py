# app/views/analise_rede.py

import streamlit as st
import pandas as pd
from layout.cards import IndicadoresResumo
from layout.charts import ChartBuilder
from layout.rankings import Rankings
from data.processor import Agrupador

def run(df: pd.DataFrame):
    st.subheader("🏪 Análise por Rede de Clientes")

    # Filtro de data
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()

    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)

    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Aplica filtros dinâmicos
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

    # Tabela por Rede e Mês
    st.subheader("📈 Evolução do Faturamento por Rede e Mês")

    tabela = df_filtrado.pivot_table(
        index='REDE',
        columns='ANO_MES',
        values='VL.BRUTO',
        aggfunc='sum'
    ).fillna(0)

    st.dataframe(tabela.style.format("R$ {:,.2f}").set_caption("Faturamento por Rede (Mês)"))

    # Ranking por Rede
    st.subheader("🏆 Ranking de Redes")
    ranking_rede = df_filtrado.groupby("REDE").agg({
        "VL.BRUTO": "sum",
        "QTDE": "sum",
        "PRECO_UNIT": "mean"
    }).sort_values(by="VL.BRUTO", ascending=False).reset_index()

    st.dataframe(ranking_rede.style.format({
        "VL.BRUTO": "R$ {:,.2f}",
        "QTDE": "{:.0f}",
        "PRECO_UNIT": "R$ {:.2f}"
    }))
