# app/layout/charts.py

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

class ChartBuilder:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def plot_preco_unitario(self):
        st.subheader("💸 Evolução do Preço Unitário por Produto")

        df_group = (
            self.df.groupby(['ANO_MES', 'COD.PRD'])['PRECO_UNIT']
            .mean()
            .reset_index()
        )

        fig = go.Figure()

        for produto in df_group['COD.PRD'].unique():
            dados = df_group[df_group['COD.PRD'] == produto]
            fig.add_trace(go.Scatter(
                x=dados['ANO_MES'],
                y=dados['PRECO_UNIT'],
                mode='lines+markers',
                name=f"{produto}",
                hovertemplate='%{x}<br>R$ %{y:.2f}<extra></extra>'
            ))

        # Linha média global
        media_global = df_group.groupby('ANO_MES')['PRECO_UNIT'].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=media_global['ANO_MES'],
            y=media_global['PRECO_UNIT'],
            mode='lines',
            name="Média Geral",
            line=dict(dash='dash', width=2, color='black'),
            hovertemplate='%{x}<br>Média R$ %{y:.2f}<extra></extra>'
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Mês/Ano",
            yaxis_title="Preço Unitário (R$)",
            hovermode="x unified",
            legend_title="Produto",
            margin=dict(t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    def plot_volume(self):
        st.subheader("📦 Evolução do Volume Vendido (Caixas)")

        df_group = (
            self.df.groupby(['ANO_MES'])['QTDE']
            .sum()
            .reset_index()
        )

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_group['ANO_MES'],
            y=df_group['QTDE'],
            text=df_group['QTDE'],
            textposition='auto',
            marker_color='steelblue',
            hovertemplate='%{x}<br>Caixas: %{y:,.0f}<extra></extra>'
        ))

        fig.update_layout(
            height=400,
            xaxis_title="Mês/Ano",
            yaxis_title="Volume (Caixas)",
            hovermode="x unified",
            margin=dict(t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)
