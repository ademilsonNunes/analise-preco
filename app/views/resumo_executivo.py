import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime
import numpy as np
from typing import List, Dict, Optional

# Configurações centralizadas
CONFIG = {
    "REAJUSTE_LIMITE": 5.0,  # Limite para considerar reajuste insuficiente (%)
    "EXPORT_FILENAME": "analise_faturamento.xlsx",
    "COLOR_PALETTE": {
        "primary": "#1f77b4",  # Azul para faturamento
        "warning": "#ff7f0e",  # Laranja para alertas
        "success": "#2ca02c",  # Verde para conformidade
    },
    "REQUIRED_COLUMNS": [
        "EMISSAO", "VL.BRUTO", "PRECO_UNIT", "DESC", "COD.PRD", "ANO_MES", "CLIENTE"
    ],
}

class DataValidator:
    """Valida a integridade do DataFrame de entrada."""
    
    @staticmethod
    def validate(df: pd.DataFrame, required_cols: List[str]) -> bool:
        """Verifica colunas obrigatórias e tipos de dados."""
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"⚠️ Colunas ausentes: {', '.join(missing_cols)}")
            return False
        
        # Verifica tipos de dados
        if not pd.api.types.is_datetime64_any_dtype(df["EMISSAO"]):
            st.error("⚠️ Coluna 'EMISSAO' deve ser do tipo datetime.")
            return False
        
        if df[["VL.BRUTO", "PRECO_UNIT", "QTDE"]].lt(0).any().any():
            st.error("⚠️ Valores negativos encontrados em 'VL.BRUTO', 'PRECO_UNIT' ou 'QTDE'.")
            return False
            
        return True

class ParetoAnalyzer:
    """Realiza análises 20/80 (Pareto) para grupos específicos."""
    
    def __init__(self, df: pd.DataFrame, group_by: str, value_col: str = "VL.BRUTO"):
        self.df = df
        self.group_by = group_by
        self.value_col = value_col
    
    def analyze(self, threshold: float = 0.8) -> pd.DataFrame:
        """Calcula o top 80% de faturamento e variações de preço."""
        grouped = self.df.groupby(self.group_by).agg({
            self.value_col: "sum",
            "PRECO_UNIT": ["first", "last", "mean"],
            "QTDE": "sum"
        }).reset_index()
        
        grouped.columns = [
            self.group_by, "FATURAMENTO", "PRECO_INICIAL", "PRECO_FINAL", 
            "PRECO_MEDIO", "VOLUME"
        ]
        
        # Calcula variação de preço
        grouped["VAR_PRECO_%"] = (
            (grouped["PRECO_FINAL"] - grouped["PRECO_INICIAL"]) / 
            grouped["PRECO_INICIAL"] * 100
        ).fillna(0).replace([np.inf, -np.inf], 0)
        
        # Calcula acumulado para Pareto
        grouped = grouped.sort_values("FATURAMENTO", ascending=False)
        grouped["ACUM_%"] = grouped["FATURAMENTO"].cumsum() / grouped["FATURAMENTO"].sum()
        
        # Adiciona classificação de reajuste
        def classify_reajuste(var: float) -> str:
            if pd.isna(var) or var == 0:
                return "Sem Reajuste"
            elif var < CONFIG["REAJUSTE_LIMITE"]:
                return f"Reajuste < {CONFIG['REAJUSTE_LIMITE']}%"
            return f"Reajuste ≥ {CONFIG['REAJUSTE_LIMITE']}%"
        
        grouped["REAJUSTE"] = grouped["VAR_PRECO_%"].apply(classify_reajuste)
        
        return grouped[grouped["ACUM_%"] <= threshold]
    
    def plot_pareto(self, title: str) -> px.bar:
        """Gera gráfico de Pareto."""
        df = self.analyze()
        df["FATURAMENTO_MILHOES"] = df["FATURAMENTO"] / 1_000_000
        
        fig = px.bar(
            df,
            x=self.group_by,
            y="FATURAMENTO_MILHOES",
            labels={"FATURAMENTO_MILHOES": "Faturamento (R$ Milhões)", self.group_by: self.group_by.capitalize()},
            title=title,
            color_discrete_sequence=[CONFIG["COLOR_PALETTE"]["primary"]]
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

class PriceElasticityAnalyzer:
    """Analisa elasticidade de preço por produto."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def calculate_elasticity(self) -> pd.DataFrame:
        """Calcula elasticidade preço-demanda por produto."""
        grouped = self.df.groupby(["COD.PRD", "DESC", "ANO_MES"]).agg({
            "PRECO_UNIT": "mean",
            "QTDE": "sum"
        }).reset_index()
        
        elasticities = []
        for (cod, desc), group in grouped.groupby(["COD.PRD", "DESC"]):
            group = group.sort_values("ANO_MES")
            if len(group) >= 2:
                price_diff = group["PRECO_UNIT"].pct_change() * 100
                qty_diff = group["QTDE"].pct_change() * 100
                elasticity = qty_diff / price_diff
                elasticity = elasticity.replace([np.inf, -np.inf], np.nan).mean()
                if not pd.isna(elasticity):
                    elasticities.append({
                        "SKU": cod,
                        "Produto": desc,
                        "Elasticidade": elasticity,
                        "Categoria": "Elástica" if abs(elasticity) > 1 else "Inelástica"
                    })
        
        return pd.DataFrame(elasticities)

class Dashboard:
    """Gerencia o dashboard Streamlit."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.validator = DataValidator()
    
    def apply_filters(self) -> pd.DataFrame:
        """Aplica filtros de data e session_state."""
        data_min = self.df["EMISSAO"].min()
        data_max = self.df["EMISSAO"].max()
        
        col1, col2 = st.sidebar.columns(2)
        data_ini = col1.date_input(
            "🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max
        )
        data_fim = col2.date_input(
            "🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max
        )
        
        df_filtered = self.df[
            (self.df["EMISSAO"] >= pd.to_datetime(data_ini)) & 
            (self.df["EMISSAO"] <= pd.to_datetime(data_fim))
        ]
        
        # Filtros adicionais
        skus = st.sidebar.multiselect("🔎 SKUs", options=self.df["COD.PRD"].unique())
        if skus:
            df_filtered = df_filtered[df_filtered["COD.PRD"].isin(skus)]
        
        return df_filtered
    
    def display_kpis(self, df: pd.DataFrame):
        """Exibe KPIs principais."""
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {df['VL.BRUTO'].sum():,.2f}")
        col2.metric("Produtos Únicos", len(df["COD.PRD"].unique()))
        col3.metric("Preço Médio", f"R$ {df['PRECO_UNIT'].mean():.2f}")
    
    def display_pareto(self, df: pd.DataFrame, group_by: str, title: str):
        """Exibe análise Pareto."""
        st.subheader(title)
        analyzer = ParetoAnalyzer(df, group_by=group_by)
        top_80 = analyzer.analyze()
        
        if top_80.empty:
            st.warning(f"⚠️ Nenhum dado disponível para {group_by.lower()}.")
            return
        
        # Formatação da tabela
        st.dataframe(
            top_80.style.format({
                "FATURAMENTO": "R$ {:,.2f}",
                "PRECO_INICIAL": "R$ {:.2f}",
                "PRECO_FINAL": "R$ {:.2f}",
                "PRECO_MEDIO": "R$ {:.2f}",
                "VAR_PRECO_%": "{:.2f}%",
                "ACUM_%": "{:.2%}",
                "VOLUME": "{:,.0f}"
            }).background_gradient(
                cmap="RdYlGn", subset=["VAR_PRECO_%"], vmin=-CONFIG["REAJUSTE_LIMITE"], vmax=CONFIG["REAJUSTE_LIMITE"]
            ),
            use_container_width=True
        )
        
        st.plotly_chart(analyzer.plot_pareto(title), use_container_width=True)
        
        # Sugestões de ações
        low_reajuste = top_80[top_80["VAR_PRECO_%"] < CONFIG["REAJUSTE_LIMITE"]]
        if not low_reajuste.empty:
            st.markdown(f"### 🔍 {group_by.capitalize()}s com Reajuste Insuficiente")
            actions = low_reajuste[[group_by, "VAR_PRECO_%"]].copy()
            actions["Ação Recomendada"] = actions.apply(
                lambda row: f"Revisar preço de {row[group_by]} (reajuste de {row['VAR_PRECO_%']:.2f}%)",
                axis=1
            )
            st.dataframe(actions, use_container_width=True)
    
    def display_elasticity(self, df: pd.DataFrame):
        """Exibe análise de elasticidade de preço."""
        st.subheader("📈 Análise de Elasticidade de Preço")
        elasticity_analyzer = PriceElasticityAnalyzer(df)
        elasticity_df = elasticity_analyzer.calculate_elasticity()
        
        if elasticity_df.empty:
            st.warning("⚠️ Dados insuficientes para análise de elasticidade.")
            return
        
        st.dataframe(
            elasticity_df.style.format({
                "Elasticidade": "{:.2f}",
            }).background_gradient(cmap="RdYlGn", subset=["Elasticidade"], vmin=-2, vmax=2),
            use_container_width=True
        )
        
        # Gráfico
        fig = px.bar(
            elasticity_df,
            x="Produto",
            y="Elasticidade",
            color="Categoria",
            title="Elasticidade Preço-Demanda por Produto",
            color_discrete_map={
                "Elástica": CONFIG["COLOR_PALETTE"]["warning"],
                "Inelástica": CONFIG["COLOR_PALETTE"]["success"]
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def export_results(self, dfs: Dict[str, pd.DataFrame]):
        """Exporta resultados para Excel."""
        st.subheader("💾 Exportar Resultados")
        if st.button("📥 Exportar para Excel"):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                for sheet_name, df in dfs.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=True)
            output.seek(0)
            st.download_button(
                "Download",
                output,
                file_name=CONFIG["EXPORT_FILENAME"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    def run(self):
        """Executa o dashboard."""
        st.title("📊 Dashboard de Faturamento e Precificação")
        
        # Validação inicial
        if not self.validator.validate(self.df, CONFIG["REQUIRED_COLUMNS"]):
            return
        
        # Filtros
        df_filtered = self.apply_filters()
        
        if df_filtered.empty:
            st.warning("⚠️ Nenhum dado disponível para os filtros selecionados. Ajuste os filtros e tente novamente.")
            return
        
        # KPIs
        self.display_kpis(df_filtered)
        
        # Análises Pareto
        with st.expander("🔍 Análise 20/80", expanded=True):
            self.display_pareto(df_filtered, "DESC", "Análise 20/80 - Produtos")
            self.display_pareto(df_filtered, "CLIENTE", "Análise 20/80 - Clientes")
            if "REDE" in df_filtered.columns:
                self.display_pareto(df_filtered, "REDE", "Análise 20/80 - Redes")
        
        # Análise de Elasticidade
        self.display_elasticity(df_filtered)
        
        # Exportação
        export_dfs = {
            "Produtos_20_80": ParetoAnalyzer(df_filtered, "DESC").analyze(),
            "Clientes_20_80": ParetoAnalyzer(df_filtered, "CLIENTE").analyze(),
        }
        if "REDE" in df_filtered.columns:
            export_dfs["Redes_20_80"] = ParetoAnalyzer(df_filtered, "REDE").analyze()
        
        self.export_results(export_dfs)
        
        # Notas Gerenciais
        st.subheader("📝 Notas e Ações Recomendadas")
        st.text_area(
            "Anotações",
            placeholder="Ex.: Revisar preços do SKU X devido a elasticidade elástica.",
            height=150
        )

def main():
    # Exemplo de uso (substituir por DataFrame real)
    df = pd.DataFrame()  # Placeholder
    dashboard = Dashboard(df)
    dashboard.run()

if __name__ == "__main__":
    main()