import streamlit as st
import pandas as pd
import plotly.express as px

def run(df: pd.DataFrame):
    st.title("📌 Positivação de Clientes")
    st.markdown("Acompanhe a presença de clientes mês a mês com análise de recompra, retorno e inatividade.")

    # ===============================
    # Clientes Ativos por Mês
    # ===============================
    clientes_por_mes = df.groupby("ANO_MES")["CLIENTE"].nunique().reset_index()
    clientes_por_mes.columns = ["ANO_MES", "Clientes Ativos"]
    fig1 = px.bar(clientes_por_mes, x="ANO_MES", y="Clientes Ativos", title="📊 Total de Clientes Ativos por Mês")
    st.plotly_chart(fig1, use_container_width=True)

    # ===============================
    # Preparação base cliente x mês
    # ===============================
    base = df.groupby(["CLIENTE", "ANO_MES"]).agg({
        "VL.BRUTO": "sum",
        "QTDE": "sum"
    }).reset_index()

    tabela_presenca = base.pivot_table(index="CLIENTE", columns="ANO_MES", values="VL.BRUTO", aggfunc="sum")
    tabela_presenca = tabela_presenca.fillna(0).applymap(lambda x: 1 if x > 0 else 0)

    # ===============================
    # Novos, Inativos e Retorno
    # ===============================
    col1, col2, col3, col4, col5 = st.columns(5)

    meses = sorted(tabela_presenca.columns)
    if len(meses) >= 2:
        mes_atual = meses[-1]
        mes_anterior = meses[-2]

        ativos_mes_atual = set(tabela_presenca[tabela_presenca[mes_atual] == 1].index)
        ativos_mes_anterior = set(tabela_presenca[tabela_presenca[mes_anterior] == 1].index)

        novos_clientes = ativos_mes_atual - ativos_mes_anterior
        clientes_inativos = ativos_mes_anterior - ativos_mes_atual
        retorno_clientes = ativos_mes_atual & ativos_mes_anterior

        total_ativos = len(ativos_mes_atual)
        taxa_recompra = len(retorno_clientes) / len(ativos_mes_anterior) * 100 if len(ativos_mes_anterior) > 0 else 0

        col1.metric("Clientes Ativos", len(ativos_mes_atual))
        col2.metric("Novos Clientes", len(novos_clientes))
        col3.metric("Clientes Inativos", len(clientes_inativos))
        col4.metric("Retorno de Clientes", len(retorno_clientes))
        col5.metric("Taxa de Recompra", f"{taxa_recompra:.1f}%")

    # ===============================
    # Heatmap Cliente x Mês
    # ===============================
    st.subheader("🧭 Mapa de Positivação (VL.BRUTO)")
    tabela_heatmap = base.pivot_table(
        index="CLIENTE", columns="ANO_MES", values="VL.BRUTO", aggfunc="sum"
    ).fillna(0)

    st.dataframe(tabela_heatmap.style.background_gradient(cmap="Blues").format("R$ {:,.0f}".format))
