import streamlit as st
import pandas as pd
import plotly.express as px
from layout.cards import indicador_simples
from data.processor import Agrupador

def run(df: pd.DataFrame):
    st.subheader("📃 Análise de Contratos Comerciais")

    # Verifica se a coluna existe
    if "CONTRATO" not in df.columns:
        st.error("A coluna CONTRATO não foi encontrada na base de dados.")
        st.stop()

    # Conversões e normalizações
    df["CONTRATO"] = pd.to_numeric(df["CONTRATO"], errors="coerce").fillna(0)
    df["VL.BRUTO"] = pd.to_numeric(df["VL.BRUTO"], errors="coerce").fillna(0)
    df["QTDE"] = pd.to_numeric(df["QTDE"], errors="coerce").fillna(0)
    df["CLIENTE"] = df["CLIENTE"].astype(str).str.strip().str.upper()
    df["ANO_MES"] = df["EMISSAO"].dt.to_period("M").astype(str)

    # Filtro por data
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()
    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("📅 Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("📅 Data Final", value=data_max, min_value=data_min, max_value=data_max)
    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Aplica filtros interativos
    df = Agrupador(df).filtrar(st.session_state.get("filtros", {}))

    df_contrato = df[df["CONTRATO"] > 0].copy()
    if df_contrato.empty:
        st.warning("⚠️ Nenhum valor de contrato encontrado com os filtros selecionados.")
        return

    # Cálculos
    df_contrato["% CONTRATO SOBRE FAT"] = (df_contrato["CONTRATO"] / df_contrato["VL.BRUTO"]) * 100
    df_contrato["CONTRATO POR CAIXA"] = (df_contrato["CONTRATO"] / df_contrato["QTDE"]).replace([float("inf"), -float("inf")], 0)

    total_contrato = df_contrato["CONTRATO"].sum()
    total_faturado = df_contrato["VL.BRUTO"].sum()
    total_caixas = df_contrato["QTDE"].sum()

    pct_medio = (total_contrato / total_faturado) * 100 if total_faturado else 0
    contrato_caixa = total_contrato / total_caixas if total_caixas else 0

    # Indicadores
    st.markdown("#### 📊 Indicadores Gerais")
    col1, col2, col3 = st.columns(3)
    indicador_simples("💸 Total em Contratos", f"R$ {total_contrato:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), col=col1)
    indicador_simples("📉 % Médio sobre Faturamento", f"{pct_medio:.2f}%", col=col2)
    indicador_simples("📦 R$ Contrato por Caixa", f"R$ {contrato_caixa:,.2f}".replace(".", ","), col=col3)

    # Evolução mensal
    st.markdown("#### 📈 Evolução Mensal de Contratos")
    mensal = df_contrato.groupby("ANO_MES").agg({"CONTRATO": "sum"}).reset_index()
    fig_mensal = px.bar(mensal, x="ANO_MES", y="CONTRATO", text="CONTRATO", title="Total de Contratos por Mês")
    st.plotly_chart(fig_mensal, use_container_width=True)

    # Top clientes
    st.markdown("#### 🧾 Clientes com Maior Volume de Contrato")
    top_cli = df_contrato.groupby("CLIENTE")["CONTRATO"].sum().sort_values(ascending=True).tail(10).reset_index()
    fig_cli = px.bar(top_cli, x="CONTRATO", y="CLIENTE", orientation="h", title="Top 10 Clientes")
    st.plotly_chart(fig_cli, use_container_width=True)

    # Top produtos
    st.markdown("#### 🧼 Produtos com Maior Valor em Contrato")
    top_prod = df_contrato.groupby("DESC")["CONTRATO"].sum().sort_values(ascending=True).tail(10).reset_index()
    fig_prod = px.bar(top_prod, x="CONTRATO", y="DESC", orientation="h", title="Top 10 Produtos com Contrato")
    st.plotly_chart(fig_prod, use_container_width=True)

    # Por rede
    if "REDE" in df_contrato.columns:
        st.markdown("#### 🏪 Contratos por Rede")
        rede = df_contrato.groupby("REDE")["CONTRATO"].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_rede = px.bar(rede, x="CONTRATO", y="REDE", orientation="h", title="Top Redes por Valor de Contrato")
        st.plotly_chart(fig_rede, use_container_width=True)

    # Por supervisor
    if "SUPERVISOR" in df_contrato.columns:
        st.markdown("#### 👤 Contratos por Supervisor")
        sup = df_contrato.groupby("SUPERVISOR")["CONTRATO"].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_sup = px.bar(sup, x="CONTRATO", y="SUPERVISOR", orientation="h", title="Top Supervisores")
        st.plotly_chart(fig_sup, use_container_width=True)

    # Por vendedor
    if "VENDEDOR" in df_contrato.columns:
        st.markdown("#### 🧑‍💼 Contratos por Vendedor")
        vend = df_contrato.groupby("VENDEDOR")["CONTRATO"].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_vend = px.bar(vend, x="CONTRATO", y="VENDEDOR", orientation="h", title="Top Vendedores")
        st.plotly_chart(fig_vend, use_container_width=True)

    # Tabela geral por cliente
    st.markdown("#### 📋 Detalhamento por Cliente")
    resumo = df_contrato.groupby("CLIENTE").agg({
        "CONTRATO": "sum",
        "VL.BRUTO": "sum",
        "QTDE": "sum"
    }).rename(columns={"VL.BRUTO": "FATURAMENTO"}).reset_index()
    resumo["% CONTRATO"] = (resumo["CONTRATO"] / resumo["FATURAMENTO"]) * 100
    resumo["R$ POR CAIXA"] = (resumo["CONTRATO"] / resumo["QTDE"]).replace([float("inf"), -float("inf")], 0)

    st.dataframe(resumo.style.format({
        "CONTRATO": "R$ {:,.2f}",
        "FATURAMENTO": "R$ {:,.2f}",
        "QTDE": "{:,.0f}",
        "% CONTRATO": "{:.2f}%",
        "R$ POR CAIXA": "R$ {:,.2f}"
    }))
    
    st.markdown("#### 🔍 Comparação: Clientes com e sem Contrato")

    clientes_com = set(df_contrato["CLIENTE"].unique())
    clientes_sem = set(df["CLIENTE"].unique()) - clientes_com
    
    qtd_com = len(clientes_com)
    qtd_sem = len(clientes_sem)
    
    vlr_com = df[df["CLIENTE"].isin(clientes_com)]["VL.BRUTO"].sum()
    vlr_sem = df[df["CLIENTE"].isin(clientes_sem)]["VL.BRUTO"].sum()
    
    comp_df = pd.DataFrame({
        "Grupo": ["Com Contrato", "Sem Contrato"],
        "Qtd Clientes": [qtd_com, qtd_sem],
        "Faturamento Total": [vlr_com, vlr_sem]
    })
    
    fig_comp = px.bar(comp_df, x="Grupo", y="Faturamento Total", color="Grupo", text_auto=True,
                      title="Faturamento: Clientes com vs. sem Contrato")
    st.plotly_chart(fig_comp, use_container_width=True)
    
    st.dataframe(comp_df.style.format({
        "Faturamento Total": "R$ {:,.2f}",
        "Qtd Clientes": "{:,.0f}"
    }))
    st.markdown("#### 🧮 Classificação por Peso Contratual (%)")
    
    def classificar_peso(percentual):
        if pd.isna(percentual) or percentual == 0:
            return "Sem Contrato"
        elif percentual <= 2:
            return "🟢 Leve"
        elif percentual <= 5:
            return "🟠 Moderado"
        else:
            return "🔴 Alto"
    
    resumo["FAIXA CONTRATO"] = resumo["% CONTRATO"].apply(classificar_peso)
    st.markdown("#### 💡 Sugestões Estratégicas por Cliente")

    def sugerir_acao(row):
        if row["% CONTRATO"] > 5:
            return "⚠️ Rever condições – contrato elevado"
        elif 2 < row["% CONTRATO"] <= 5:
            return "🔍 Monitorar contrato"
        elif 0 < row["% CONTRATO"] <= 2:
            return "✅ Contrato saudável"
        else:
            return "📞 Avaliar proposta de contrato"
    
    resumo["SUGESTAO"] = resumo.apply(sugerir_acao, axis=1)
    
    st.dataframe(resumo[[
        "CLIENTE", "FATURAMENTO", "CONTRATO", "QTDE",
        "% CONTRATO", "R$ POR CAIXA", "FAIXA CONTRATO", "SUGESTAO"
    ]].sort_values(by="% CONTRATO", ascending=False).style.format({
        "FATURAMENTO": "R$ {:,.2f}",
        "CONTRATO": "R$ {:,.2f}",
        "QTDE": "{:,.0f}",
        "% CONTRATO": "{:.2f}%",
        "R$ POR CAIXA": "R$ {:,.2f}"
    }))

    fig_faixa = px.pie(
        resumo,
        names="FAIXA CONTRATO",
        values="FATURAMENTO",
        title="Distribuição de Clientes por Faixa de Contrato"
    )
    st.plotly_chart(fig_faixa, use_container_width=True)
    # Exportação
    st.markdown("#### 💾 Exportar Dados")
    if st.button("📥 Exportar para Excel"):
        nome_arquivo = "analise_contratos.xlsx"
        with pd.ExcelWriter(nome_arquivo, engine="xlsxwriter") as writer:
            df_contrato.to_excel(writer, sheet_name="Dados_Filtrados", index=False)
            
            resumo[[
                "CLIENTE", "FATURAMENTO", "CONTRATO", "QTDE",
                "% CONTRATO", "R$ POR CAIXA", "FAIXA CONTRATO", "SUGESTAO"
            ]].to_excel(writer, sheet_name="Resumo_Cliente", index=False)
      
        with open(nome_arquivo, "rb") as f:
            st.download_button("⬇️ Baixar Arquivo", f, file_name=nome_arquivo)
