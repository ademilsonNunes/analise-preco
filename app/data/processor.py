import pandas as pd
import streamlit as st

class Agrupador:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def filtrar(self, filtros: dict) -> pd.DataFrame:
        df_filtrado = self.df.copy()
        for chave, valor in filtros.items():
            if chave in df_filtrado.columns:
                if isinstance(valor, list):  # multiselect
                    if "Todos" not in valor:
                        df_filtrado = df_filtrado[df_filtrado[chave].isin(valor)]
                elif valor != "Todos":
                    df_filtrado = df_filtrado[df_filtrado[chave] == valor]
        return df_filtrado


    def exibir_tabela(self, df: pd.DataFrame):
        st.subheader("📄 Tabela Detalhada")
        st.dataframe(
            df[[
                "CLIENTE", "COD.PRD", "DESC", "EMISSAO",
                "QTDE", "PRECO_UNIT", "VL.BRUTO", "SUPERVISOR", "VENDEDOR", "TP"
            ]].sort_values(by="EMISSAO", ascending=False)
        )
