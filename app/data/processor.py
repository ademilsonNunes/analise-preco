import pandas as pd
import streamlit as st
from typing import Dict

class Agrupador:
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def filtrar(self, filtros: Dict) -> pd.DataFrame:
        df_filtrado = self.df.copy()
        
        for coluna, valor in filtros.items():
            if valor is not None:  # Ignorar filtros não selecionados
                if isinstance(valor, list):
                    # Suportar filtros múltiplos com isin
                    df_filtrado = df_filtrado[df_filtrado[coluna].isin(valor)]
                else:
                    # Suportar filtros únicos com ==
                    df_filtrado = df_filtrado[df_filtrado[coluna] == valor]
        
        return df_filtrado


    def exibir_tabela(self, df: pd.DataFrame):
        st.subheader("📄 Tabela Detalhada")
        st.dataframe(
            df[[
                "CLIENTE", "COD.PRD", "DESC", "EMISSAO",
                "QTDE", "PRECO_UNIT", "VL.BRUTO", "SUPERVISOR", "VENDEDOR", "TP"
            ]].sort_values(by="EMISSAO", ascending=False)
        )
