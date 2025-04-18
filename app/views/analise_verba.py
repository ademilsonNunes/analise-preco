import streamlit as st
import pandas as pd
import plotly.express as px
from layout.cards import indicador_simples
from data.processor import Agrupador

def run(df: pd.DataFrame):
    st.subheader("💰 Análise de Investimentos (VERBA)")

    # Filtro de datas
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()
    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)
    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Parâmetros
    #st.markdown("#### ⚙️ Parâmetros de Análise")
    #margem_bruta_pct = st.slider("Margem Bruta Estimada (%)", 0.0, 100.0, 35.0, step=0.5)

    # Filtra VERBA
    df_verba = df[df["DESC"].str.upper().str.startswith("VERBA")]
    df_verba = Agrupador(df_verba).filtrar(st.session_state.get("filtros", {}))
    
    if df_verba.empty:
        st.warning("⚠️ Nenhum lançamento de VERBA encontrado com os filtros selecionados.")
        return
    
    # 🧼 Normaliza CLIENTE
    df_verba["CLIENTE"] = df_verba["CLIENTE"].astype(str).str.strip().str.upper()
    df["CLIENTE"] = df["CLIENTE"].astype(str).str.strip().str.upper()
    
    # 🧮 Converte valores para numérico
    df["QTDE"] = pd.to_numeric(df["QTDE"], errors="coerce")
    df["VL.BRUTO"] = pd.to_numeric(df["VL.BRUTO"], errors="coerce")
    
    # 🧾 Filtra vendas e aplica filtros
    df_venda = df[df["NATUREZA"] == "VENDA"]
    df_venda = Agrupador(df_venda).filtrar(st.session_state.get("filtros", {}))
    
    # 📊 Agrega por cliente
    vendas_agrupadas = df_venda.groupby("CLIENTE").agg({
        "VL.BRUTO": "sum",
        "QTDE": "sum"
    }).rename(columns={"VL.BRUTO": "FATURAMENTO", "QTDE": "CAIXAS"})
    
    verba_por_cliente = df_verba.groupby("CLIENTE")["VL.BRUTO"].sum().rename("INVESTIMENTO")
    
    # 🧩 Merge consolidado
    comparativo = pd.concat([verba_por_cliente, vendas_agrupadas], axis=1).fillna(0)
    comparativo["% SOBRE FATURAMENTO"] = (
        comparativo["INVESTIMENTO"] / comparativo["FATURAMENTO"].replace(0, pd.NA)
    ) * 100
    comparativo["INVESTIMENTO POR CAIXA"] = (
        comparativo["INVESTIMENTO"] / comparativo["CAIXAS"].replace(0, pd.NA)
    )

    # Indicadores principais
    st.markdown("#### 📊 Indicadores de Investimento")
    total_verba = df_verba["VL.BRUTO"].sum()

    df_venda = df[df["NATUREZA"] == "VENDA"]
    df_venda = Agrupador(df_venda).filtrar(st.session_state.get("filtros", {}))
    vendas_agrupadas = df_venda.groupby("CLIENTE").agg({
        "VL.BRUTO": "sum",
        "QTDE": "sum"
    }).rename(columns={"VL.BRUTO": "FATURAMENTO", "QTDE": "CAIXAS"})

    verba_por_cliente = df_verba.groupby("CLIENTE")["VL.BRUTO"].sum().rename("INVESTIMENTO")
    comparativo = pd.concat([verba_por_cliente, vendas_agrupadas], axis=1).fillna(0)
    comparativo["% SOBRE FATURAMENTO"] = (comparativo["INVESTIMENTO"] / comparativo["FATURAMENTO"]) * 100
    comparativo["INVESTIMENTO POR CAIXA"] = (comparativo["INVESTIMENTO"] / comparativo["CAIXAS"]).replace([float("inf"), -float("inf")], 0)

    total_faturado = comparativo["FATURAMENTO"].sum()
    total_caixas = comparativo["CAIXAS"].sum()
    pct_verba = (total_verba / total_faturado) * 100 if total_faturado else 0
    verba_por_caixa = total_verba / total_caixas if total_caixas else 0

    col1, col2, col3 = st.columns(3)
    indicador_simples("💰 Total Investido (VERBA)", f"R$ {total_verba:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), col=col1)
    indicador_simples("📦 R$ por Caixa Vendida", f"R$ {verba_por_caixa:,.2f}".replace(".", ","), col=col2)
    indicador_simples("📉 % Sobre o Faturamento", f"{pct_verba:.2f}%", col=col3)

    # Top clientes
    st.markdown("#### 🧾 Clientes com Maior Investimento")
    top_invest = comparativo.sort_values("INVESTIMENTO", ascending=True).tail(10).reset_index()
    fig_cli = px.bar(top_invest, x="INVESTIMENTO", y="CLIENTE", orientation="h",
                     title="Top 10 Clientes por Investimento (VERBA)")
    st.plotly_chart(fig_cli, use_container_width=True)

    # Top produtos
    #st.markdown("#### 📦 Produtos com Mais Verba Aplicada")
    #top_prod = df_verba.groupby("COD.PRD").agg({"VL.BRUTO": "sum"}).reset_index()
    #produtos = df[["COD.PRD", "DESC"]].drop_duplicates().set_index("COD.PRD")
    #top_prod = top_prod.join(produtos, on="COD.PRD").fillna("Produto não encontrado")
    #top_prod = top_prod.sort_values("VL.BRUTO", ascending=True).tail(10)
    #fig_prod = px.bar(top_prod, x="VL.BRUTO", y="DESC", orientation="h",
    #                  title="Top 10 Produtos com Verba Investida")
    #st.plotly_chart(fig_prod, use_container_width=True)

    # Por Rede
    if "REDE" in df_verba.columns:
        st.markdown("#### 🏪 Verba por Rede de Clientes")
        verba_rede = df_verba.groupby("REDE")["VL.BRUTO"].sum().sort_values(ascending=True).reset_index()
        fig_rede = px.bar(verba_rede.tail(10), x="VL.BRUTO", y="REDE", orientation="h",
                          title="Top 10 Redes com Investimento (VERBA)")
        st.plotly_chart(fig_rede, use_container_width=True)

    # Dispersão
    st.markdown("#### 📉 Dispersão: Investimento x Faturamento por Cliente")
    fig_disp = px.scatter(
        comparativo.reset_index(),
        x="INVESTIMENTO",
        y="FATURAMENTO",
        text="CLIENTE",
        size="INVESTIMENTO",
        color="% SOBRE FATURAMENTO",
        labels={"INVESTIMENTO": "R$ Investido", "FATURAMENTO": "R$ Faturado"},
        title="Clientes - Investimento vs Faturamento"
    )
    fig_disp.update_traces(textposition="top center")
    st.plotly_chart(fig_disp, use_container_width=True)

    # Classificação Estratégica
    st.markdown("#### 🧠 Classificação Estratégica de Clientes (A/B/C/D)")

    def classificar_cliente(row):
        if row["INVESTIMENTO"] >= comparativo["INVESTIMENTO"].median() and row["FATURAMENTO"] >= comparativo["FATURAMENTO"].median():
            return "A - Manter/Expandir"
        elif row["INVESTIMENTO"] >= comparativo["INVESTIMENTO"].median() and row["FATURAMENTO"] < comparativo["FATURAMENTO"].median():
            return "B - Monitorar"
        elif row["INVESTIMENTO"] < comparativo["INVESTIMENTO"].median() and row["FATURAMENTO"] >= comparativo["FATURAMENTO"].median():
            return "C - Potencial"
        else:
            return "D - Baixa Prioridade"

    def sugestao_acao(row):
        if row["CLASSIFICACAO"].startswith("A"):
            return "✅ Excelente desempenho – manter estratégia"
        elif row["CLASSIFICACAO"].startswith("B"):
            if row["% SOBRE FATURAMENTO"] > 20:
                return "⚠️ Revisar política de verba"
            else:
                return "🔄 Considerar renegociação"
        elif row["CLASSIFICACAO"].startswith("C"):
            return "📈 Potencial para incremento de mix"
        else:
            if row["INVESTIMENTO"] > 0:
                return "🛑 Descontinuar verba"
            else:
                return "🧪 Cliente com baixo histórico – avaliar nova abordagem"

    comparativo["CLASSIFICACAO"] = comparativo.apply(classificar_cliente, axis=1)
    comparativo["SUGESTAO_ACAO"] = comparativo.apply(sugestao_acao, axis=1)

    st.dataframe(comparativo.reset_index()[[
        "CLIENTE", "CLASSIFICACAO", "INVESTIMENTO", "FATURAMENTO", "CAIXAS",
        "% SOBRE FATURAMENTO", "INVESTIMENTO POR CAIXA", "SUGESTAO_ACAO"
    ]].sort_values("CLASSIFICACAO").style.format({
        "INVESTIMENTO": "R$ {:,.2f}",
        "FATURAMENTO": "R$ {:,.2f}",
        "CAIXAS": "{:,.0f}",
        "% SOBRE FATURAMENTO": "{:.2f}%",
        "INVESTIMENTO POR CAIXA": "R$ {:,.2f}"
    }))

    # Pizza
    st.markdown("#### 🥧 Distribuição por Classificação Estratégica")
    fig_pizza = px.pie(
        comparativo.reset_index(),
        names="CLASSIFICACAO",
        values="INVESTIMENTO",
        title="Distribuição dos Investimentos por Classificação"
    )
    st.plotly_chart(fig_pizza, use_container_width=True)

    # Treemap
    st.markdown("#### 🗂️ Treemap de Investimentos por Cliente")
    
    df_treemap = comparativo.reset_index()
    df_treemap = df_treemap[df_treemap["INVESTIMENTO"] > 0]
    
    if df_treemap.empty:
        st.warning("⚠️ Não há dados suficientes com investimento > 0 para gerar o treemap.")
    else:
        fig_tree = px.treemap(
            df_treemap,
            path=["CLASSIFICACAO", "CLIENTE"],
            values="INVESTIMENTO",
            color="% SOBRE FATURAMENTO",
            color_continuous_scale="RdYlGn",
            title="Distribuição de Verba por Cliente (Treemap)"
        )
    st.plotly_chart(fig_tree, use_container_width=True)


    # Exportação
    st.markdown("#### 💾 Exportar Dados")
    if st.button("📥 Exportar para Excel"):
        nome_arquivo = "investimentos_verba_completo.xlsx"
        with pd.ExcelWriter(nome_arquivo, engine="xlsxwriter") as writer:
            df_verba.to_excel(writer, sheet_name="Verba_Lancamentos", index=False)
            comparativo.reset_index().to_excel(writer, sheet_name="Resumo_Cliente", index=False)
            top_prod.reset_index(drop=True).to_excel(writer, sheet_name="Resumo_Produto", index=False)
            if "REDE" in df_verba.columns:
                verba_rede.to_excel(writer, sheet_name="Resumo_Rede", index=False)
        with open(nome_arquivo, "rb") as f:
            st.download_button("⬇️ Baixar Arquivo", f, file_name=nome_arquivo)
