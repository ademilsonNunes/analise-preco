import streamlit as st
import pandas as pd
import plotly.express as px
from layout.cards import indicador_simples
from data.processor import Agrupador

def run(df: pd.DataFrame):
    st.subheader("↩️ Análise de Devoluções")

    # Filtro de datas
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()
    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)

    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Filtra apenas devoluções
    df_dev = df[df["NATUREZA"] == "DEVOLUCAO"]
    df_dev = Agrupador(df_dev).filtrar(st.session_state.get("filtros", {}))

    if df_dev.empty:
        st.warning("⚠️ Nenhuma devolução encontrada com os filtros selecionados.")
        return

    # Indicadores
    st.markdown("#### 📊 Indicadores de Devolução")

    volume_dev = df_dev["QTDE"].sum()
    valor_dev = df_dev["VL.BRUTO"].sum()

    # Se houver vendas no mesmo filtro, calcular taxa de devolução
    df_venda = df[df["NATUREZA"] == "VENDA"]
    df_venda = Agrupador(df_venda).filtrar(st.session_state.get("filtros", {}))
    volume_venda = df_venda["QTDE"].sum()
    taxa_dev = (volume_dev / volume_venda) * 100 if volume_venda else 0

    col1, col2, col3 = st.columns(3)
    indicador_simples("📦 Volume Devolvido", f"{volume_dev:,.0f}".replace(",", "."), col=col1)
    indicador_simples("💸 Valor Devolvido", f"R$ {valor_dev:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), col=col2)
    indicador_simples("📉 Taxa de Devolução", f"{taxa_dev:.2f}%", col=col3)

    # Gráfico de evolução mensal
    st.markdown("#### 📈 Evolução Mensal de Devoluções")
    devolucao_mensal = df_dev.groupby("ANO_MES").agg({"QTDE": "sum", "VL.BRUTO": "sum"}).reset_index()
    fig = px.bar(devolucao_mensal, x="ANO_MES", y="QTDE", text="QTDE", title="Volume Devolvido por Mês")
    st.plotly_chart(fig, use_container_width=True)

    # Motivos e áreas de devolução
    if "MOTDEST" in df_dev.columns and "AREDESC" in df_dev.columns:
        st.markdown("#### 📋 Motivos e Áreas de Devolução")
        col1, col2 = st.columns(2)

        motivos = df_dev.groupby("MOTDEST")["QTDE"].sum().sort_values(ascending=True).reset_index()
        fig_motivo = px.bar(motivos.tail(10), x="QTDE", y="MOTDEST", orientation="h", title="Top 10 Motivos de Devolução")
        col1.plotly_chart(fig_motivo, use_container_width=True)

        areas = df_dev.groupby("AREDESC")["QTDE"].sum().sort_values(ascending=True).reset_index()
        fig_area = px.bar(areas.tail(10), x="QTDE", y="AREDESC", orientation="h", title="Top 10 Áreas com Devolução")
        col2.plotly_chart(fig_area, use_container_width=True)

    # Ranking de produtos e clientes
    st.markdown("#### 🏷️ Produtos com Mais Devoluções")
    top_prod = df_dev.groupby("DESC").agg({"QTDE": "sum"}).sort_values("QTDE", ascending=True).tail(10).reset_index()
    fig_prod = px.bar(top_prod, x="QTDE", y="DESC", orientation="h", title="Top 10 Produtos Devolvidos")
    st.plotly_chart(fig_prod, use_container_width=True)

    st.markdown("#### 👥 Clientes com Mais Devoluções")
    top_cli = df_dev.groupby("CLIENTE").agg({"QTDE": "sum"}).sort_values("QTDE", ascending=True).tail(10).reset_index()
    fig_cli = px.bar(top_cli, x="QTDE", y="CLIENTE", orientation="h", title="Top 10 Clientes que Mais Devolvem")
    st.plotly_chart(fig_cli, use_container_width=True)

    # Taxa de devolução por produto
    if not df_venda.empty:
        st.markdown("#### 📌 Taxa de Devolução por Produto")
        base = pd.concat([df_venda, df_dev])
        resumo = base.groupby(["DESC", "NATUREZA"]).agg({"QTDE": "sum"}).reset_index()
        pivot = resumo.pivot(index="DESC", columns="NATUREZA", values="QTDE").fillna(0)
        pivot["% Devolvido"] = (pivot["DEVOLUCAO"] / (pivot["VENDA"] + pivot["DEVOLUCAO"])) * 100
        pivot = pivot.reset_index()
        st.dataframe(pivot.style.format({
            "VENDA": "{:,.0f}",
            "DEVOLUCAO": "{:,.0f}",
            "% Devolvido": "{:.2f}%"
        }))

    # Exportação
    st.markdown("#### 💾 Exportar Dados")
    if st.button("📥 Exportar para Excel"):
        nome_arquivo = "devolucoes_resumo.xlsx"
        with pd.ExcelWriter(nome_arquivo, engine="xlsxwriter") as writer:
            df_dev.to_excel(writer, sheet_name="Devolucoes", index=False)
            devolucao_mensal.to_excel(writer, sheet_name="Evolucao_Mensal", index=False)
            if not df_venda.empty:
                pivot.to_excel(writer, sheet_name="Taxa_Dev_Produto", index=False)
        with open(nome_arquivo, "rb") as f:
            st.download_button("⬇️ Baixar Arquivo", f, file_name=nome_arquivo)
