# app/pages/resumo_executivo.py

import streamlit as st
import pandas as pd
import plotly.express as px
from layout.cards import IndicadoresResumo
from layout.charts import ChartBuilder
from data.processor import Agrupador
from layout.rankings import Rankings


def run(df: pd.DataFrame):
    st.subheader("📌 Visão Geral do Faturamento")

    # Filtro de datas
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()
    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input("🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max)
    data_fim = col2.date_input("🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max)

    df = df[(df["EMISSAO"] >= pd.to_datetime(data_ini)) & (df["EMISSAO"] <= pd.to_datetime(data_fim))]

    # Filtros laterais (session)
    processor = Agrupador(df)
    filtros = st.session_state.get("filtros", {})
    df_filtrado = processor.filtrar(filtros)

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")
        return

    # Indicadores
    IndicadoresResumo(df_filtrado).exibir()

    # Gráficos
    charts = ChartBuilder(df_filtrado)
    charts.plot_preco_unitario()
    charts.plot_volume()

    # 📊 Tabela de preço unitário por SKU com "DESC" como rótulo
    st.subheader("📊 Evolução do Preço Unitário por SKU e Mês")

    tabela_preco = df_filtrado.pivot_table(
        index=["DESC", "COD.PRD"],
        columns="ANO_MES",
        values="PRECO_UNIT",
        aggfunc="mean"
    ).sort_index(axis=1)

    variacao = tabela_preco.pct_change(axis=1) * 100
    variacao.columns = [f"{col} (%)" for col in variacao.columns]
    tabela_final = pd.concat([tabela_preco, variacao], axis=1)

    st.dataframe(
        tabela_final.style
        .format("{:.2f}")
        .background_gradient(cmap='RdYlGn', axis=None, subset=variacao.columns)
        .set_caption("💡 Preço Unitário Médio por Produto e Variação %")
    )

    # 🧠 Análise 20/80: Produtos que representam 80% do faturamento
    st.subheader("📌 Análise - Produtos que representam 80% do faturamento")

    df_total = df_filtrado.groupby(["DESC", "COD.PRD"]).agg({
        "VL.BRUTO": "sum",
        "QTDE": "sum",
        "PRECO_UNIT": "mean"
    }).reset_index()

    df_total = df_total.sort_values("VL.BRUTO", ascending=False)
    df_total["ACUM%"] = df_total["VL.BRUTO"].cumsum() / df_total["VL.BRUTO"].sum()

    top_80 = df_total[df_total["ACUM%"] <= 0.80]
    st.dataframe(top_80.style.format({"VL.BRUTO": "R$ {:,.2f}", "PRECO_UNIT": "{:.2f}"}))

    # 🧠 Análise 20/80: Produtos que representam 80% do faturamento
    # 🔁 Bloco adicional: Pareto + Reajustes insuficientes
    # Gráfico de Pareto: Faturamento acumulado dos produtos
    st.markdown("### 📉 Curva de Pareto dos Produtos")
    top_80_plot = df_total.copy()
    top_80_plot["ACUM%"] = top_80_plot["VL.BRUTO"].cumsum() / top_80_plot["VL.BRUTO"].sum()
    top_80_plot["ACUM%"] = top_80_plot["ACUM%"] * 100
    top_80_plot["VL.BRUTO_MILHÕES"] = top_80_plot["VL.BRUTO"] / 1_000_000
    
    fig_pareto = px.bar(
        top_80_plot,
        x="DESC",
        y="VL.BRUTO_MILHÕES",
        labels={"VL.BRUTO_MILHÕES": "Faturamento (R$ Milhões)", "DESC": "Produto"},
        title="Curva de Pareto - Produtos por Faturamento",
    )
    fig_pareto.add_scatter(
        x=top_80_plot["DESC"],
        y=top_80_plot["ACUM%"],
        mode="lines+markers",
        name="% Acumulado",
        yaxis="y2",
    )
    
    fig_pareto.update_layout(
        yaxis2=dict(
            overlaying="y",
            side="right",
            title="% Acumulado",
            range=[0, 100]
        ),
        height=500
    )
    st.plotly_chart(fig_pareto, use_container_width=True)
    
    # Produtos no 20/80 com reajuste < 5%
    st.markdown("### 🔍 Produtos do Top 80% com Reajuste Inferior a 5%")
    
    produtos_var = df_filtrado.groupby(["DESC", "COD.PRD", "ANO_MES"]).agg({
        "PRECO_UNIT": "mean"
    }).reset_index()
    
    reajustes_baixos = []
    
    for (desc, cod), grupo in produtos_var.groupby(["DESC", "COD.PRD"]):
        grupo = grupo.sort_values("ANO_MES")
        if len(grupo) >= 2:
            preco_ini = grupo["PRECO_UNIT"].iloc[0]
            preco_fim = grupo["PRECO_UNIT"].iloc[-1]
            variacao_pct = ((preco_fim - preco_ini) / preco_ini) * 100
            if abs(variacao_pct) < 5:
                # Verifica se o produto está no top 80%
                if cod in top_80["COD.PRD"].values:
                    reajustes_baixos.append({
                        "Produto": desc,
                        "SKU": cod,
                        "Preço Inicial": preco_ini,
                        "Preço Final": preco_fim,
                        "Variação Preço %": variacao_pct
                    })
    
    df_reajustes = pd.DataFrame(reajustes_baixos)
    if not df_reajustes.empty:
        st.dataframe(df_reajustes.style.format({
            "Preço Inicial": "R$ {:.2f}",
            "Preço Final": "R$ {:.2f}",
            "Variação Preço %": "{:.2f}%"
        }))
    else:
        st.success("✅ Todos os produtos no top 80% tiveram aumento igual ou superior a 5%.")
    

    # Avaliação de reajuste de preço para produtos 20/80
    st.markdown("🔎 Produtos com reajuste de preço **inferior a 5%** dentro dos 80% de faturamento:")

    df_mes = df_filtrado.groupby(["COD.PRD", "DESC", "ANO_MES"]).agg({"PRECO_UNIT": "mean"}).reset_index()
    variacoes = []

    for (cod, desc), grupo in df_mes.groupby(["COD.PRD", "DESC"]):
        grupo = grupo.sort_values("ANO_MES")
        if len(grupo) >= 2:
            preco_ini = grupo["PRECO_UNIT"].iloc[0]
            preco_fim = grupo["PRECO_UNIT"].iloc[-1]
            variacao = ((preco_fim - preco_ini) / preco_ini) * 100
            if abs(variacao) < 5:
                variacoes.append({"SKU": cod, "Produto": desc, "Variação Preço %": variacao})

    df_var = pd.DataFrame(variacoes)
    if not df_var.empty:
        st.dataframe(df_var.style.format({"Variação Preço %": "{:.2f}%"}))
    else:
        st.success("✅ Todos os principais produtos tiveram reajuste superior a 5%.")

    # Rankings convencionais
    Rankings(df_filtrado).exibir()

    # ================================
    # 📊 ANÁLISE 20/80 POR CLIENTE E REDE
    # ================================
    
    st.subheader("🧮 Análise 20/80: Reajuste de Preço por Cliente e Rede")
    
    def analisar_20_80(df: pd.DataFrame, grupo: str):
        agrupado = df.groupby(grupo).agg({
            "VL.BRUTO": "sum",
            "PRECO_UNIT": ["first", "last"]
        }).reset_index()
    
        agrupado.columns = [grupo, "FATURAMENTO", "PRECO_INICIAL", "PRECO_FINAL"]
        agrupado["VAR_PRECO_%"] = ((agrupado["PRECO_FINAL"] - agrupado["PRECO_INICIAL"]) / agrupado["PRECO_INICIAL"]) * 100
    
        agrupado = agrupado.sort_values("FATURAMENTO", ascending=False)
        agrupado["FAT_ACUM"] = agrupado["FATURAMENTO"].cumsum() / agrupado["FATURAMENTO"].sum()
    
        top_80 = agrupado[agrupado["FAT_ACUM"] <= 0.80].copy()
    
        def classificar(var):
            if pd.isna(var):
                return "Sem Dados"
            elif var == 0:
                return "Sem Reajuste"
            elif var < 5:
                return "Reajuste < 5%"
            else:
                return "Reajuste ≥ 5%"
    
        top_80["REAJUSTE"] = top_80["VAR_PRECO_%"].apply(classificar)
    
        return top_80
    
    # CLIENTES
    df_clientes_80 = analisar_20_80(df_filtrado, "CLIENTE")
    st.markdown("### 👥 Clientes (80% do faturamento)")
    st.dataframe(df_clientes_80[[ "CLIENTE", "PRECO_INICIAL", "PRECO_FINAL", "VAR_PRECO_%", "REAJUSTE"]],
                 use_container_width=True)
    
    cliente_fig = px.histogram(df_clientes_80, x="REAJUSTE", color="REAJUSTE",
        title="Distribuição de Reajustes entre os Principais Clientes",
        labels={"REAJUSTE": "Faixa de Reajuste"},
    )
    st.plotly_chart(cliente_fig, use_container_width=True)
    
    # REDES
    if "REDE" in df_filtrado.columns:
        df_rede_80 = analisar_20_80(df_filtrado, "REDE")
        st.markdown("### 🏪 Redes (80% do faturamento)")
        st.dataframe(df_rede_80[[ "REDE", "PRECO_INICIAL", "PRECO_FINAL", "VAR_PRECO_%", "REAJUSTE"]],
                     use_container_width=True)
    
        rede_fig = px.histogram(df_rede_80, x="REAJUSTE", color="REAJUSTE",
            title="Distribuição de Reajustes entre as Principais Redes",
            labels={"REAJUSTE": "Faixa de Reajuste"},
        )
        st.plotly_chart(rede_fig, use_container_width=True)
    
        # ===== NOVA SEÇÃO: Análise 20/80 de Clientes e Redes =====
        st.markdown("## 🧠 Análise 20/80 – Clientes e Redes com Potencial de Ação Estratégica")
    
        def analisar_variacao_preco(df, grupo):
            df_media = df.groupby([grupo, "ANO_MES"]).agg({
                "PRECO_UNIT": "mean",
                "VL.BRUTO": "sum"
            }).reset_index()
    
            pivot = df_media.pivot(index=grupo, columns="ANO_MES", values="PRECO_UNIT")
            variacao = pivot.pct_change(axis=1).fillna(0).replace([float('inf'), -float('inf')], 0)
            ultima_var = variacao.iloc[:, -1] * 100
    
            df_total = df.groupby(grupo)["VL.BRUTO"].sum().reset_index().sort_values("VL.BRUTO", ascending=False)
            df_total["ACUM"] = df_total["VL.BRUTO"].cumsum() / df_total["VL.BRUTO"].sum()
    
            grupo_80 = df_total[df_total["ACUM"] <= 0.8][grupo].tolist()
    
            resultado = pd.DataFrame({
                grupo: grupo_80,
                "VAR_PRECO_%": ultima_var.loc[grupo_80]
            }).set_index(grupo)
    
            def classificar(var):
                if pd.isna(var): return "Sem Dados"
                if var == 0: return "🔴 Sem aumento"
                elif var < 5: return "🟠 Aumento < 5%"
                else: return "🟢 Aumento ≥ 5%"
    
            resultado["CATEGORIA"] = resultado["VAR_PRECO_%"].apply(classificar)
            return resultado
    
        for grupo in ["CLIENTE", "REDE"]:
            resultado = analisar_variacao_preco(df_filtrado, grupo)
            st.markdown(f"### 🎯 {grupo}s que representam 80% do faturamento")
            st.dataframe(resultado.style.format({"VAR_PRECO_%": "{:.2f}%"}))
    
            grafico = resultado.reset_index().groupby("CATEGORIA")[grupo].count().reset_index()
            fig = px.bar(grafico, x="CATEGORIA", y=grupo, text=grupo, color="CATEGORIA",
                         title=f"Distribuição de {grupo}s por Variação de Preço")
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
        # ===== Exportação e Notas =====
        st.markdown("## 💾 Exportar e Anotações")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("📥 Exportar Tabela para Excel"):
                output = pd.ExcelWriter("analise_20_80.xlsx", engine="xlsxwriter")
                for grupo in ["CLIENTE", "REDE"]:
                    resultado = analisar_variacao_preco(df_filtrado, grupo)
                    resultado.to_excel(output, sheet_name=f"{grupo}_20_80")
                output.close()
                with open("analise_20_80.xlsx", "rb") as f:
                    st.download_button("Download", f, file_name="analise_20_80.xlsx")
    
        with col2:
            st.text_area("📝 Notas Gerenciais", height=150, placeholder="Escreva aqui observações e ações sugeridas...")

    