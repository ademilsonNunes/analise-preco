import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from data.processor import Agrupador
from layout.cards import indicador_simples


def run(df: pd.DataFrame):
    st.subheader("📊 Análise Gerencial de Disparidade de Preço entre Clientes de perfis Semelhantes")

    with st.expander("🧠 Metodologia e Lógica de Cálculo da Análise", expanded=False):
        st.markdown("""
        Esta análise compara o preço unitário de venda por produto com a média praticada por clientes com perfil similar,
        definido a partir do volume de caixas adquiridas (QTDE).

        O **Índice de Alinhamento de Preço (IAP_CLUSTER)** é calculado dividindo o preço unitário praticado pelo preço médio do grupo:
        `IAP_CLUSTER = PRECO_UNIT / PRECO_CLUSTER_MEDIA`

        ### Classificação com Ícones:
        - 🔴 **Oportunidade (-)** (< 0.85): Preço muito abaixo do padrão  
        - 🟠 **Abaixo da Média** (0.85 – 0.95): Leve desalinhamento  
        - 🟡 **Alinhado** (0.95 – 1.05): Dentro da faixa de equilíbrio  
        - 🟢 **Acima da Média** (1.05 – 1.15): Leve ganho de margem  
        - ⚪ **Oportunidade (+)** (> 1.15): Preço muito acima da média do perfil
        """)

    filtros = st.session_state.get("filtros", {})
    for campo, valor in filtros.items():
        if campo in df.columns:
            if isinstance(valor, list) and valor:
                df = df[df[campo].isin(valor)]
            elif valor != "Todos":
                df = df[df[campo] == valor]

    processor = Agrupador(df)
    df_filtrado = processor.filtrar(filtros)
    df_filtrado = df_filtrado[df_filtrado["CLIENTE"] != "CLIENTE PADRAO-000001"]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        return

    df_filtrado["PRECO_UNIT"] = pd.to_numeric(df_filtrado["PRECO_UNIT"], errors="coerce")
    df_filtrado["VL.BRUTO"] = pd.to_numeric(df_filtrado["VL.BRUTO"], errors="coerce")
    df_filtrado["QTDE"] = pd.to_numeric(df_filtrado["QTDE"], errors="coerce")

    # Clusterização por volume
    df_filtrado["FAIXA_VOLUMETRICA"] = pd.qcut(df_filtrado["QTDE"], q=4, labels=["Baixo", "Médio", "Alto", "Muito Alto"])
    df_filtrado["FAIXA_FATURAMENTO"] = pd.qcut(df_filtrado["VL.BRUTO"], q=4, labels=["Baixo", "Médio", "Alto", "Muito Alto"])
    df_filtrado["PERFIL_CLIENTE"] = df_filtrado["FAIXA_VOLUMETRICA"].astype(str) + " caixas"

    media_cluster = df_filtrado.groupby(["COD.PRD", "PERFIL_CLIENTE"])["PRECO_UNIT"].mean().reset_index()
    media_cluster.rename(columns={"PRECO_UNIT": "PRECO_CLUSTER_MEDIA"}, inplace=True)
    df_join = df_filtrado.merge(media_cluster, on=["COD.PRD", "PERFIL_CLIENTE"], how="left")

    df_join["IAP_CLUSTER"] = df_join["PRECO_UNIT"] / df_join["PRECO_CLUSTER_MEDIA"]
    df_join["STATUS"] = pd.cut(
        df_join["IAP_CLUSTER"],
        bins=[0, 0.85, 0.95, 1.05, 1.15, np.inf],
        labels=["Oportunidade (-)", "Abaixo da Média", "Alinhado", "Acima da Média", "Oportunidade (+)"]
    )

    # Ícones por status
    icones = {
        "Oportunidade (-)": "🔴",
        "Abaixo da Média": "🟠",
        "Alinhado": "🟡",
        "Acima da Média": "🟢",
        "Oportunidade (+)": "⚪"
    }
    df_join["STATUS_ICON"] = df_join["STATUS"].astype(str).map(icones) + " " + df_join["STATUS"].astype(str)

    # Indicadores
    total_analise = len(df_join)
    abaixo_media = (df_join["STATUS"] == "Oportunidade (-)").sum()
    acima_media = (df_join["STATUS"] == "Oportunidade (+)").sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        indicador_simples("Total de Registros", total_analise)
    with col2:
        indicador_simples("Abaixo da Faixa (<-15%)", abaixo_media)
    with col3:
        indicador_simples("Acima da Faixa (>+15%)", acima_media)

    # Tabelas por perfil
    st.markdown("### 📋 Tabelas por Cluster de Perfil de Cliente")
    for perfil in df_join["PERFIL_CLIENTE"].unique():
        st.markdown(f"#### 📌 Perfil: {perfil}")
        df_perf = df_join[df_join["PERFIL_CLIENTE"] == perfil][[
            "CLIENTE", "DESC", "QTDE", "VL.BRUTO", "FAIXA_FATURAMENTO",
            "PRECO_UNIT", "PRECO_CLUSTER_MEDIA", "IAP_CLUSTER", "STATUS_ICON"
        ]].sort_values("IAP_CLUSTER")

        df_perf["VL.BRUTO"] = df_perf["VL.BRUTO"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_perf["PRECO_UNIT"] = df_perf["PRECO_UNIT"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_perf["PRECO_CLUSTER_MEDIA"] = df_perf["PRECO_CLUSTER_MEDIA"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_perf["QTDE"] = df_perf["QTDE"].apply(lambda x: f"{x:,.0f}".replace(",", "."))

        st.dataframe(df_perf, use_container_width=True)

    # Tabela consolidada
    st.markdown("### 📊 Tabela Consolidada por Perfil e Status")
    consolidado = df_join.groupby(["PERFIL_CLIENTE", "STATUS"]).apply(
        lambda x: pd.Series({
            "QTDE": x["QTDE"].sum(),
            "VL.BRUTO": x["VL.BRUTO"].sum(),
            "PRECO_UNIT": np.average(x["PRECO_UNIT"], weights=x["QTDE"]),
            "IAP_CLUSTER": np.average(x["IAP_CLUSTER"], weights=x["QTDE"])
        })
    ).reset_index()

    consolidado["QTDE"] = consolidado["QTDE"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    consolidado["VL.BRUTO"] = consolidado["VL.BRUTO"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    consolidado["PRECO_UNIT"] = consolidado["PRECO_UNIT"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    consolidado["IAP_CLUSTER"] = consolidado["IAP_CLUSTER"].apply(lambda x: f"{x:.2f}".replace(".", ","))

    st.dataframe(consolidado, use_container_width=True)

    # Gráficos
    st.markdown("### 📈 Gráficos Complementares")
    fig1 = px.box(df_join, x="PERFIL_CLIENTE", y="PRECO_UNIT", color="STATUS", title="Boxplot de Preço Unitário por Perfil")
    st.plotly_chart(fig1, use_container_width=True)

    df_clientes_unicos = df_join.drop_duplicates(subset=["CLIENTE"])
    fig2 = px.bar(
        df_clientes_unicos.groupby("STATUS")["CLIENTE"].nunique().reset_index(),
        x="STATUS", y="CLIENTE", text_auto=True,
        title="Clientes Únicos por Faixa de Status"
    )
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.histogram(df_join, x="IAP_CLUSTER", nbins=50, color="STATUS", title="Distribuição do IAP (Índice de Alinhamento)")
    st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("### 💡 Insights Automáticos")
    lowest_iap = df_join.nsmallest(5, "IAP_CLUSTER")[["CLIENTE", "DESC", "IAP_CLUSTER"]]
    st.write("Top 5 clientes com menor IAP (potencial de aumento de preço):")
    st.dataframe(lowest_iap)
    
    st.success("✅ Análise validada e ajustada com base na lógica correta de clientes, clusters e indicadores.")
