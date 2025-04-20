import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import numpy as np
from typing import List, Dict
from data.processor import Agrupador
from layout.cards import IndicadoresResumo
from layout.charts import ChartBuilder
from layout.rankings import Rankings

# Configurações
CONFIG = {
    "REAJUSTE_LIMITE": 5.0,
    "EXPORT_FILENAME": "analise_faturamento.xlsx",
    "COLOR_PALETTE": {
        "primary": "#1f77b4",
        "warning": "#ff7f0e",
        "success": "#2ca02c",
    },
    "REQUIRED_COLUMNS": [
        "EMISSAO", "VL.BRUTO", "PRECO_UNIT", "DESC", "COD.PRD", "ANO_MES", "CLIENTE", "QTDE", "NATUREZA", "VENDEDOR"
    ],
}

class DataValidator:
    """Valida a integridade do DataFrame."""
    @staticmethod
    def validate(df: pd.DataFrame, required_cols: List[str]) -> bool:
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"⚠️ Colunas ausentes: {', '.join(missing_cols)}")
            return False
        if not pd.api.types.is_datetime64_any_dtype(df["EMISSAO"]):
            st.error("⚠️ Coluna 'EMISSAO' deve ser do tipo datetime.")
            return False
        mask_venda = df["NATUREZA"] == "VENDA"
        if mask_venda.any() and df[mask_venda][["VL.BRUTO", "PRECO_UNIT", "QTDE"]].lt(0).any().any():
            st.error("⚠️ Valores negativos encontrados em 'VL.BRUTO', 'PRECO_UNIT' ou 'QTDE' para VENDA.")
            return False
        return True

class ParetoAnalyzer:
    """Realiza análises 20/80."""
    def __init__(self, df: pd.DataFrame, group_by: str, value_col: str = "VL.BRUTO"):
        self.df = df
        self.group_by = group_by
        self.value_col = value_col
    
    def analyze(self, threshold: float = 0.8) -> pd.DataFrame:
        if self.group_by == "VENDEDOR":
            # Para group_by="VENDEDOR", não precisamos selecionar um vendedor
            grouped = self.df.groupby(self.group_by).agg({
                self.value_col: "sum",
                "PRECO_UNIT": ["first", "last", "mean"],
                "QTDE": "sum"
            }).reset_index()
            grouped.columns = [
                self.group_by, "FATURAMENTO", "PRECO_INICIAL", "PRECO_FINAL", "PRECO_MEDIO", "VOLUME"
            ]
        else:
            # Selecionar o vendedor com maior faturamento por group_by
            vendedor_agg = self.df.groupby([self.group_by, "VENDEDOR"]).agg({
                self.value_col: "sum"
            }).reset_index()
            vendedor_max = vendedor_agg.loc[vendedor_agg.groupby(self.group_by)[self.value_col].idxmax()]
            
            # Agregar métricas principais
            grouped = self.df.groupby(self.group_by).agg({
                self.value_col: "sum",
                "PRECO_UNIT": ["first", "last", "mean"],
                "QTDE": "sum"
            }).reset_index()
            grouped.columns = [
                self.group_by, "FATURAMENTO", "PRECO_INICIAL", "PRECO_FINAL", "PRECO_MEDIO", "VOLUME"
            ]
            
            # Mesclar com vendedor selecionado
            grouped = grouped.merge(
                vendedor_max[[self.group_by, "VENDEDOR"]],
                on=self.group_by,
                how="left"
            )
        
        grouped["VAR_PRECO_%"] = (
            (grouped["PRECO_FINAL"] - grouped["PRECO_INICIAL"]) / grouped["PRECO_INICIAL"] * 100
        ).fillna(0).replace([np.inf, -np.inf], 0)
        grouped = grouped.sort_values("FATURAMENTO", ascending=False)
        grouped["ACUM_%"] = grouped["FATURAMENTO"].cumsum() / grouped["FATURAMENTO"].sum()
        grouped["REAJUSTE"] = grouped["VAR_PRECO_%"].apply(
            lambda x: "Sem Reajuste" if x == 0 else f"Reajuste < {CONFIG['REAJUSTE_LIMITE']}%" if x < CONFIG["REAJUSTE_LIMITE"] else f"Reajuste ≥ {CONFIG['REAJUSTE_LIMITE']}%"
        )
        return grouped[grouped["ACUM_%"] <= threshold]
    
    def plot_pareto(self, title: str) -> px.bar:
        df = self.analyze()
        df["FATURAMENTO_MILHOES"] = df["FATURAMENTO"] / 1_000_000
        hover_data = ["VENDEDOR"] if self.group_by != "VENDEDOR" else []
        fig = px.bar(
            df,
            x=self.group_by,
            y="FATURAMENTO_MILHOES",
            labels={"FATURAMENTO_MILHOES": "Faturamento (R$ Milhões)", self.group_by: self.group_by.capitalize()},
            title=title,
            color_discrete_sequence=[CONFIG["COLOR_PALETTE"]["primary"]],
            hover_data=hover_data
        )
        fig.add_scatter(
            x=df[self.group_by],
            y=df["ACUM_%"] * 100,
            mode="lines+markers",
            name="% Acumulado",
            yaxis="y2",
            line=dict(color=CONFIG["COLOR_PALETTE"]["success"])
        )
        fig.update_layout(
            yaxis2=dict(overlaying="y", side="right", title="% Acumulado", range=[0, 100]),
            height=500,
            showlegend=True,
            hovermode="x unified"
        )
        return fig

class VendedorAnalyzer:
    """Calcula métricas por vendedor."""
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def analyze(self) -> pd.DataFrame:
        grouped = self.df[self.df["NATUREZA"] == "VENDA"].groupby("VENDEDOR").agg({
            "VL.BRUTO": "sum",
            "QTDE": "sum",
            "CLIENTE": "nunique",
            "PRECO_UNIT": ["first", "last"]
        }).reset_index()
        grouped.columns = [
            "VENDEDOR", "FATURAMENTO", "VOLUME", "CLIENTES_DISTINTOS", "PRECO_INICIAL", "PRECO_FINAL"
        ]
        grouped["TICKET_MEDIO"] = grouped["FATURAMENTO"] / grouped["CLIENTES_DISTINTOS"]
        grouped["VAR_PRECO_%"] = (
            (grouped["PRECO_FINAL"] - grouped["PRECO_INICIAL"]) / grouped["PRECO_INICIAL"] * 100
        ).fillna(0).replace([np.inf, -np.inf], 0)
        return grouped.sort_values("FATURAMENTO", ascending=False)

class Dashboard:
    """Gerencia o dashboard Resumo Executivo."""
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.validator = DataValidator()
        self.processor = Agrupador(df)
    
    def apply_filters(self) -> pd.DataFrame:
        data_min = self.df["EMISSAO"].min()
        data_max = self.df["EMISSAO"].max()
        col1, col2 = st.sidebar.columns(2)
        data_ini = col1.date_input(
            "🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max
        )
        data_fim = col2.date_input(
            "🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max
        )
    
        # Primeiro aplica o filtro por data
        df_filtered = self.df[
            (self.df["EMISSAO"] >= pd.to_datetime(data_ini)) &
            (self.df["EMISSAO"] <= pd.to_datetime(data_fim))
        ]
    
        # Depois aplica os demais filtros
        filtros = st.session_state.get("filtros", {})
        df_filtered = Agrupador(df_filtered).filtrar(filtros)
    
        return df_filtered

    
    def display_pareto(self, df: pd.DataFrame, group_by: str, title: str):
        st.subheader(title)
        analyzer = ParetoAnalyzer(df, group_by=group_by)
        top_80 = analyzer.analyze()
        if top_80.empty:
            st.warning(f"⚠️ Nenhum dado disponível para {group_by.lower()}.")
            return
        st.dataframe(
            top_80.style.format({
                "FATURAMENTO": "R$ {:,.2f}",
                "PRECO_INICIAL": "R$ {:.2f}",
                "PRECO_FINAL": "R$ {:.2f}",
                "PRECO_MEDIO": "R$ {:.2f}",
                "VAR_PRECO_%": "{:.2f}%",
                "ACUM_%": "{:.2%}",
                "VOLUME": "{:,.0f}"
            }).background_gradient(cmap="RdYlGn", subset=["VAR_PRECO_%"]),
            use_container_width=True
        )
        st.plotly_chart(analyzer.plot_pareto(title), use_container_width=True)
        low_reajuste = top_80[top_80["VAR_PRECO_%"] < CONFIG["REAJUSTE_LIMITE"]]
        if not low_reajuste.empty:
            st.markdown(f"### 🔍 {group_by.capitalize()}s com Reajuste < {CONFIG['REAJUSTE_LIMITE']}%")
            columns = [group_by, "VENDEDOR", "VAR_PRECO_%"] if group_by != "VENDEDOR" else [group_by, "VAR_PRECO_%"]
            actions = low_reajuste[columns].copy()
            actions["Ação Recomendada"] = actions.apply(
                lambda row: f"Revisar preço de {row[group_by]} (reajuste de {row['VAR_PRECO_%']:.2f}%)"
                            if group_by == "VENDEDOR" else
                            f"Revisar preço de {row[group_by]} com vendedor {row['VENDEDOR']} (reajuste de {row['VAR_PRECO_%']:.2f}%)",
                axis=1
            )
            st.dataframe(actions, use_container_width=True)
    
    def display_preco_table(self, df: pd.DataFrame):
        st.subheader("📊 Evolução do Preço Unitário por SKU, Vendedor e Mês")
        tabela_preco = df.pivot_table(
            index=["DESC", "COD.PRD", "VENDEDOR"],
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
            .set_caption("💡 Preço Unitário Médio por Produto, Vendedor e Variação %"),
            use_container_width=True
        )
    
    def display_vendedor_metrics(self, df: pd.DataFrame):
        st.subheader("📈 Métricas por Vendedor")
        analyzer = VendedorAnalyzer(df)
        metrics = analyzer.analyze()
        if metrics.empty:
            st.warning("⚠️ Nenhum dado disponível para análise de vendedores.")
            return
        st.dataframe(
            metrics.style.format({
                "FATURAMENTO": "R$ {:,.2f}",
                "VOLUME": "{:,.0f}",
                "CLIENTES_DISTINTOS": "{:,.0f}",
                "PRECO_INICIAL": "R$ {:.2f}",
                "PRECO_FINAL": "R$ {:.2f}",
                "TICKET_MEDIO": "R$ {:,.2f}",
                "VAR_PRECO_%": "{:.2f}%"
            }).background_gradient(cmap="RdYlGn", subset=["VAR_PRECO_%"]),
            use_container_width=True
        )
    
    def export_results(self, dfs: Dict[str, pd.DataFrame]):
        st.subheader("💾 Exportar Resultados")
        if st.button("📥 Exportar para Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                for sheet_name, df in dfs.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            output.seek(0)
            st.download_button(
                label="⬇️ Baixar Excel",
                data=output,
                file_name=CONFIG["EXPORT_FILENAME"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    def run(self):
        if not self.validator.validate(self.df, CONFIG["REQUIRED_COLUMNS"]):
            st.stop()
        
        st.subheader("📌 Visão Geral do Faturamento")
        
        df_filtered = self.apply_filters()
        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")
            return
        
        IndicadoresResumo(df_filtered).exibir()
        
        charts = ChartBuilder(df_filtered)
        charts.plot_preco_unitario()
        charts.plot_volume()
        
        self.display_preco_table(df_filtered)
        
        self.display_vendedor_metrics(df_filtered)
        
        with st.expander("📊 Análise Pareto", expanded=True):
            tabs = st.tabs(["Produtos", "Clientes", "Redes", "Vendedores"])
            with tabs[0]:
                self.display_pareto(df_filtered, group_by="COD.PRD", title="Top 80% Produtos por Faturamento")
            with tabs[1]:
                self.display_pareto(df_filtered, group_by="CLIENTE", title="Top 80% Clientes por Faturamento")
            with tabs[2]:
                if "REDE" in df_filtered.columns:
                    self.display_pareto(df_filtered, group_by="REDE", title="Top 80% Redes por Faturamento")
                else:
                    st.warning("⚠️ Coluna 'REDE' não encontrada nos dados.")
            with tabs[3]:
                self.display_pareto(df_filtered, group_by="VENDEDOR", title="Top 80% Vendedores por Faturamento")
        
        Rankings(df_filtered).exibir()
        
        export_dfs = {
            "Produtos": ParetoAnalyzer(df_filtered, group_by="COD.PRD").analyze(),
            "Clientes": ParetoAnalyzer(df_filtered, group_by="CLIENTE").analyze(),
            "Vendedores": ParetoAnalyzer(df_filtered, group_by="VENDEDOR").analyze(),
        }
        if "REDE" in df_filtered.columns:
            export_dfs["Redes"] = ParetoAnalyzer(df_filtered, group_by="REDE").analyze()
        self.export_results(export_dfs)