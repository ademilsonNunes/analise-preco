# app/layout/filters.py

import streamlit as st
import pandas as pd

class FiltroDinamico:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def exibir_filtros(self):
        with st.sidebar.expander("🔍 Filtros", expanded=True):
            col1, col2 = st.columns(2)
            supervisor = col1.selectbox("👨‍💼 Supervisor", ["Todos"] + sorted(self.df["SUPERVISOR"].dropna().unique().tolist()))
            rede = col2.selectbox("🏪 Rede", ["Todos"] + sorted(self.df["REDE"].dropna().unique().tolist()))

            col3, col4 = st.columns(2)
            vendedor = col3.selectbox("🧍‍♂️ Vendedor", ["Todos"] + sorted(self.df["VENDEDOR"].dropna().unique().tolist()))
            cliente = col4.selectbox("👥 Cliente", ["Todos"] + sorted(self.df["CLIENTE"].dropna().unique().tolist()))

            col5, col6 = st.columns(2)
            produto = col5.selectbox("🧼 Produto", ["Todos"] + sorted(self.df["DESC"].dropna().unique().tolist()))
            sku = col6.selectbox("🔢 SKU", ["Todos"] + sorted(self.df["COD.PRD"].dropna().unique().tolist()))
            natureza = st.multiselect(
                "🧾 Tipo de Registro (Natureza)",
                ["VENDA", "BONIFICACAO", "DEVOLUCAO", "INVESTIMENTO"],
                default=["VENDA"]
            )
        return {
            "SUPERVISOR": supervisor,
            "REDE": rede,
            "VENDEDOR": vendedor,
            "CLIENTE": cliente,
            "DESC": produto,
            "COD.PRD": sku,
            "NATUREZA": natureza
        }
        
