# app/views/bonificacoes.py

import streamlit as st
import pandas as pd
import plotly.express as px
from layout.cards import indicador_simples
from data.processor import Agrupador

def run(df: pd.DataFrame):
    st.subheader("🎁 Visão de Bonificações")

    # Filtro de datas
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()
    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)

    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Filtra apenas bonificações
    df_boni = df[df["NATUREZA"] == "BONIFICACAO"]
    df_boni = Agrupador(df_boni).filtrar(st.session_state.get("filtros", {}))

    if df_boni.empty:
        st.warning("⚠️ Nenhuma bonificação encontrada com os filtros selecionados.")
        return

    st.markdown("#### 🔢 Indicadores Gerais")

    total_bonificado = df_boni["QTDE"].sum()
    valor_aprox = df_boni["VL.BRUTO"].sum()

    col1, col2 = st.columns(2)
    indicador_simples("📦 Qtde Bonificada", f"{total_bonificado:,.0f}".replace(",", "."),
                      col=col1)
    indicador_simples("💰 Valor Aproximado", f"R$ {valor_aprox:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                      col=col2)

    # ==============================
    # 📊 Evolução mensal
    # ==============================
    st.markdown("#### 📈 Evolução Mensal de Bonificações")

    df_boni_mensal = df_boni.groupby("ANO_MES").agg({"QTDE": "sum"}).rename(columns={"QTDE": "QTDE_BONI"})

    # Se houver vendas no filtro, incluímos comparativo
    df_venda = df[df["NATUREZA"] == "VENDA"]
    df_venda = Agrupador(df_venda).filtrar(st.session_state.get("filtros", {}))

    if not df_venda.empty:
        df_venda_mensal = df_venda.groupby("ANO_MES").agg({"QTDE": "sum"}).rename(columns={"QTDE": "QTDE_VENDA"})
        comparativo = pd.concat([df_boni_mensal, df_venda_mensal], axis=1).fillna(0)
        comparativo["% BONI"] = (comparativo["QTDE_BONI"] / (comparativo["QTDE_VENDA"] + comparativo["QTDE_BONI"])) * 100
        fig = px.bar(comparativo.reset_index(), x="ANO_MES", y=["QTDE_BONI", "QTDE_VENDA"],
                     barmode="group", text_auto=True, title="Volume Bonificado e Vendido por Mês")
        fig.add_scatter(x=comparativo.index, y=comparativo["% BONI"],
                        mode="lines+markers", name="% Bonificação", yaxis="y2")
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", title="% Bonificação", range=[0, 100]),
            height=400
        )
    else:
        comparativo = df_boni_mensal.reset_index()
        fig = px.bar(comparativo, x="ANO_MES", y="QTDE_BONI", text="QTDE_BONI", title="Volume Bonificado por Mês")

    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # 📊 Comparativo Venda x Bonificação por Produto
    # ==============================
    st.markdown("#### 🔄 Comparativo: Venda x Bonificação por Produto")

    base = pd.concat([df_venda, df_boni])
    resumo = base.groupby(["DESC", "NATUREZA"]).agg({"QTDE": "sum"}).reset_index()
    pivot = resumo.pivot(index="DESC", columns="NATUREZA", values="QTDE").fillna(0)
    pivot["% Bonificado"] = (pivot["BONIFICACAO"] / (pivot["VENDA"] + pivot["BONIFICACAO"])) * 100
    pivot = pivot.reset_index()

    st.dataframe(pivot.style.format({
        "VENDA": "{:,.0f}".format,
        "BONIFICACAO": "{:,.0f}".format,
        "% Bonificado": "{:.2f}%".format
    }))

    # ==============================
    # 🏆 Rankings
    # ==============================
    st.markdown("#### 🏆 Produtos Mais Bonificados")
    prod_boni = df_boni.groupby("DESC").agg({"QTDE": "sum", "VL.BRUTO": "sum"}).reset_index()
    fig_prod = px.bar(prod_boni.sort_values("QTDE", ascending=True).tail(10),
                      x="QTDE", y="DESC", orientation="h", title="Top 10 Produtos Bonificados",
                      labels={"QTDE": "Qtde Bonificada", "DESC": "Produto"})
    st.plotly_chart(fig_prod, use_container_width=True)

    st.markdown("#### 👥 Clientes com Mais Bonificações")
    cli_boni = df_boni.groupby("CLIENTE").agg({"QTDE": "sum", "VL.BRUTO": "sum"}).reset_index()
    fig_cli = px.bar(cli_boni.sort_values("QTDE", ascending=True).tail(10),
                     x="QTDE", y="CLIENTE", orientation="h", title="Top 10 Clientes Bonificados",
                     labels={"QTDE": "Qtde Bonificada", "CLIENTE": "Cliente"})
    st.plotly_chart(fig_cli, use_container_width=True)

    # ==============================
    # 💾 Exportação
    # ==============================
    st.markdown("#### 💾 Exportar Dados")
    if st.button("📥 Exportar para Excel"):
        nome_arquivo = "bonificacoes_resumo.xlsx"
        with pd.ExcelWriter(nome_arquivo, engine="xlsxwriter") as writer:
            df_boni.to_excel(writer, sheet_name="Bonificacoes", index=False)
            pivot.to_excel(writer, sheet_name="Comparativo", index=False)
            if not df_venda.empty:
                comparativo.to_excel(writer, sheet_name="Evolucao_Mensal", index=True)
        with open(nome_arquivo, "rb") as f:
            st.download_button("⬇️ Baixar Arquivo", f, file_name=nome_arquivo)
