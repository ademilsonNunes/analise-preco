import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional
from layout.cards import IndicadoresResumo
from layout.charts import ChartBuilder
from data.processor import Agrupador
from layout.rankings import Rankings
from io import StringIO

class ProductAnalyzer:
    """Analisador de dados detalhados por produto."""
    REQUIRED_COLUMNS = ["EMISSAO", "ANO_MES", "COD.PRD", "DESC", "PRECO_UNIT", "VL.BRUTO", "QTDE", "NATUREZA"]
    MAX_TABLE_ROWS = 10000

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.validate_data()

    def validate_data(self) -> None:
        """Valida se o DataFrame contém todas as colunas necessárias."""
        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_cols:
            st.error(f"⚠️ Colunas ausentes no DataFrame: {', '.join(missing_cols)}")
            st.stop()
        if not pd.api.types.is_datetime64_any_dtype(self.df["EMISSAO"]):
            st.error("⚠️ Coluna 'EMISSAO' deve ser do tipo datetime.")
            st.stop()

    def calculate_evolution(self, selected_products: Optional[list] = None) -> pd.DataFrame:
        """Calcula a evolução de preço e volume por produto, filtrando por produtos selecionados."""
        df_venda = self.df[self.df["NATUREZA"] == "VENDA"]
        if df_venda.empty:
            return pd.DataFrame()
        evolucao = df_venda.groupby(["ANO_MES", "COD.PRD", "DESC"]).agg({
            "PRECO_UNIT": "mean",
            "VL.BRUTO": "sum",
            "QTDE": "sum"
        }).reset_index()
        if selected_products and selected_products != ["Todos"]:
            evolucao = evolucao[evolucao["COD.PRD"].isin(selected_products)]
        return evolucao

    def calculate_ranking(self, top_n: int = 10) -> pd.DataFrame:
        """Calcula o ranking de produtos com maior crescimento médio de preço."""
        df_venda = self.df[self.df["NATUREZA"] == "VENDA"]
        if df_venda.empty:
            return pd.DataFrame(columns=["COD.PRD", "DESC", "Crescimento Médio (%)"])
        
        # Calcular preço médio mensal por produto
        preco_mensal = df_venda.groupby(["COD.PRD", "DESC", "ANO_MES"])["PRECO_UNIT"].mean().reset_index()
        
        # Calcular crescimento percentual entre meses consecutivos
        preco_mensal = preco_mensal.sort_values(["COD.PRD", "ANO_MES"])
        preco_mensal["Crescimento"] = preco_mensal.groupby("COD.PRD")["PRECO_UNIT"].pct_change() * 100
        
        # Média de crescimento por produto
        ranking = preco_mensal.groupby(["COD.PRD", "DESC"])["Crescimento"].mean().reset_index()
        ranking = ranking.dropna().sort_values("Crescimento", ascending=False).head(top_n)
        ranking.columns = ["COD.PRD", "DESC", "Crescimento Médio (%)"]
        return ranking

    def display_detailed_table(self) -> None:
        """Exibe uma tabela detalhada dos dados filtrados, com limite de linhas e opção de download."""
        df_venda = self.df[self.df["NATUREZA"] == "VENDA"]
        if df_venda.empty:
            st.warning("⚠️ Nenhum dado disponível para a tabela detalhada.")
            return
        
        tabela = df_venda[["ANO_MES", "COD.PRD", "DESC", "PRECO_UNIT", "QTDE", "VL.BRUTO"]].copy()
        
        # Limitar número de linhas para renderização
        total_rows = len(tabela)
        if total_rows > self.MAX_TABLE_ROWS:
            st.warning(
                f"⚠️ A tabela contém {total_rows:,} linhas, mas apenas as primeiras {self.MAX_TABLE_ROWS:,} "
                "serão exibidas. Use o botão abaixo para baixar os dados completos."
            )
            tabela_display = tabela.head(self.MAX_TABLE_ROWS)
        else:
            tabela_display = tabela
        
        # Renderizar tabela com formatação
        st.dataframe(
            tabela_display.style.format({
                "PRECO_UNIT": "R$ {:.2f}",
                "QTDE": "{:,.0f}",
                "VL.BRUTO": "R$ {:,.2f}"
            }).set_caption("📄 Detalhamento por Produto"),
            use_container_width=True
        )
        
        # Botão para download da tabela completa
        csv_buffer = StringIO()
        tabela.to_csv(csv_buffer, index=False, encoding="utf-8")
        st.download_button(
            label="📥 Baixar Tabela Completa (CSV)",
            data=csv_buffer.getvalue(),
            file_name="detalhamento_produto.csv",
            mime="text/csv",
            key="download_tabela_detalhada"
        )

def run(df: pd.DataFrame) -> None:
    """Executa a análise detalhada por produto."""
    st.subheader("📦 Análise Detalhada por Produto")

    # Validação inicial
    analyzer = ProductAnalyzer(df)

    # Filtro de datas
    data_min = df["EMISSAO"].min()
    data_max = df["EMISSAO"].max()
    col1, col2 = st.sidebar.columns(2)
    data_ini = col1.date_input(
        "🗓️ Data Inicial", value=data_min, min_value=data_min, max_value=data_max
    )
    data_fim = col2.date_input(
        "🗓️ Data Final", value=data_max, min_value=data_min, max_value=data_max
    )

    df_filtered = df[
        (df["EMISSAO"] >= pd.to_datetime(data_ini)) & 
        (df["EMISSAO"] <= pd.to_datetime(data_fim))
    ]

    # Aplica filtros do session_state
    filtros = st.session_state.get("filtros", {})
    processor = Agrupador(df_filtered)
    df_filtrado = processor.filtrar(filtros)

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para os filtros selecionados.")
        return

    # Atualizar analyzer com df_filtrado
    analyzer.df = df_filtrado

    # Indicadores
    resumo = IndicadoresResumo(df_filtrado)
    resumo.exibir()

    # Gráficos principais
    charts = ChartBuilder(df_filtrado)
    charts.plot_preco_unitario()
    charts.plot_volume()

    # Filtro de produtos para evolução
    st.subheader("📊 Evolução de Preço Unitário por Produto ao Longo do Tempo")
    produtos = ["Todos"] + sorted(df_filtrado["COD.PRD"].dropna().unique().tolist())
    selected_products = st.multiselect(
        "🔹 Selecionar Produtos",
        produtos,
        default=["Todos"],
        key="filtro_produtos_evolucao"
    )
    if "Todos" in selected_products:
        selected_products = None

    # Evolução mensal por produto
    evolucao = analyzer.calculate_evolution(selected_products)
    if evolucao.empty:
        st.warning("⚠️ Nenhum dado disponível para a evolução dos produtos selecionados.")
    else:
        for _, grupo in evolucao.groupby(["COD.PRD", "DESC"]):
            sku = grupo["COD.PRD"].iloc[0]
            desc = grupo["DESC"].iloc[0]
            st.markdown(f"#### 🔹 Produto: `{sku} - {desc}`")
            col1, col2 = st.columns(2)

            with col1:
                fig_preco = px.line(
                    grupo,
                    x="ANO_MES",
                    y="PRECO_UNIT",
                    title="Preço Unitário Médio (R$)",
                    labels={"PRECO_UNIT": "Preço (R$)", "ANO_MES": "Mês/Ano"},
                    height=250
                )
                fig_preco.update_layout(showlegend=False, margin=dict(t=30))
                st.plotly_chart(fig_preco, use_container_width=True, key=f"preco_{sku}")

            with col2:
                fig_volume = px.bar(
                    grupo,
                    x="ANO_MES",
                    y="QTDE",
                    title="Volume Vendido (Unidades)",
                    labels={"QTDE": "Volume", "ANO_MES": "Mês/Ano"},
                    height=250
                )
                fig_volume.update_layout(showlegend=False, margin=dict(t=30))
                st.plotly_chart(fig_volume, use_container_width=True, key=f"volume_{sku}")

    # Ranking de crescimento
    st.subheader("🏆 Produtos com Maior Crescimento de Preço (Média Mensal)")
    ranking_df = analyzer.calculate_ranking()
    if ranking_df.empty:
        st.warning("⚠️ Nenhum dado disponível para o ranking de crescimento.")
    else:
        st.dataframe(
            ranking_df.style.format({"Crescimento Médio (%)": "{:.2f}%"})
                    .background_gradient(cmap="RdYlGn", subset=["Crescimento Médio (%)"]),
            use_container_width=True
        )

    # Tabela detalhada
    st.subheader("📄 Detalhamento do Produto")
    analyzer.display_detailed_table()