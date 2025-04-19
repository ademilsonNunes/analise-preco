import streamlit as st
import pandas as pd

class FiltroDinamico:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def exibir_filtros(self):
        with st.sidebar.expander("🔍 Filtros", expanded=True):
            filtros_resultado = {}

            def gerar_selectbox(coluna, label, key, emoji=""):
                if coluna in self.df.columns:
                    opcoes = ["Todos"] + sorted(self.df[coluna].dropna().astype(str).unique().tolist())
                    valor_padrao = st.session_state["filtros"].get(coluna, "Todos")
                    return st.selectbox(f"{emoji} {label}", opcoes, index=opcoes.index(valor_padrao) if valor_padrao in opcoes else 0, key=key)
                return "Todos"

            col1, col2 = st.columns(2)
            filtros_resultado["SUPERVISOR"] = gerar_selectbox("SUPERVISOR", "Supervisor", "filtro_supervisor", "👨‍💼")
            filtros_resultado["REDE"] = gerar_selectbox("REDE", "Rede", "filtro_rede", "🏪")

            col3, col4 = st.columns(2)
            filtros_resultado["VENDEDOR"] = gerar_selectbox("VENDEDOR", "Vendedor", "filtro_vendedor", "🧍‍♂️")
            filtros_resultado["CLIENTE"] = gerar_selectbox("CLIENTE", "Cliente", "filtro_cliente", "👥")

            col5, col6 = st.columns(2)
            filtros_resultado["DESC"] = gerar_selectbox("DESC", "Produto", "filtro_produto", "🧼")
            filtros_resultado["COD.PRD"] = gerar_selectbox("COD.PRD", "SKU", "filtro_sku", "🔢")

            if "NATUREZA" in self.df.columns:
                filtros_resultado["NATUREZA"] = gerar_selectbox("NATUREZA", "Natureza", "filtro_natureza", "📦")

        return filtros_resultado
