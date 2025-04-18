# app/layout/rankings.py
import streamlit as st
import pandas as pd
import plotly.express as px

class Rankings:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def exibir(self):
        st.subheader("🏆 Top 10 Rankings de Faturamento e Volume")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧼 Produtos com Maior Faturamento")
            top_produtos = self.df.groupby("COD.PRD")["VL.BRUTO"].sum().nlargest(10).reset_index()
            fig_prod = px.bar(top_produtos, x="VL.BRUTO", y="COD.PRD", orientation="h",
                              labels={"VL.BRUTO": "Faturamento", "COD.PRD": "Produto"},
                              text_auto=".2s")
            fig_prod.update_layout(height=300, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_prod, use_container_width=True)

        with col2:
            st.markdown("### 👥 Clientes com Maior Faturamento")
            top_clientes = self.df.groupby("CLIENTE")["VL.BRUTO"].sum().nlargest(10).reset_index()
            fig_cli = px.bar(top_clientes, x="VL.BRUTO", y="CLIENTE", orientation="h",
                             labels={"VL.BRUTO": "Faturamento", "CLIENTE": "Cliente"},
                             text_auto=".2s")
            fig_cli.update_layout(height=300, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_cli, use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.markdown("### 📦 Produtos com Maior Volume Vendido")
            top_volume = self.df.groupby("COD.PRD")["QTDE"].sum().nlargest(10).reset_index()
            fig_vol = px.bar(top_volume, x="QTDE", y="COD.PRD", orientation="h",
                             labels={"QTDE": "Caixas", "COD.PRD": "Produto"},
                             text_auto=".2s")
            fig_vol.update_layout(height=300, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_vol, use_container_width=True)

        if "SUP" in self.df.columns:
            with col4:
                st.markdown("### 🧑‍💼 Supervisores com Maior Faturamento")
                top_sup = self.df.groupby("SUP")["VL.BRUTO"].sum().nlargest(10).reset_index()
                fig_sup = px.bar(top_sup, x="VL.BRUTO", y="SUP", orientation="h",
                                 labels={"VL.BRUTO": "Faturamento", "SUP": "Supervisor"},
                                 text_auto=".2s")
                fig_sup.update_layout(height=300, yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_sup, use_container_width=True)

    def exibir_ranking_por_produto(self):
        st.subheader("📌 Evolução Mensal por Produto")

        ranking = self.df.groupby(["COD.PRD", "ANO_MES"]).agg({
            "VL.BRUTO": "sum",
            "QTDE": "sum",
            "PRECO_UNIT": "mean"
        }).reset_index()

        fig = px.line(
            ranking,
            x="ANO_MES",
            y="PRECO_UNIT",
            color="COD.PRD",
            markers=True,
            labels={"PRECO_UNIT": "Preço Médio", "ANO_MES": "Mês"},
            title="📈 Evolução do Preço Médio por Produto"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
