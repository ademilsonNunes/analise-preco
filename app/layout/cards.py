import streamlit as st

class IndicadoresResumo:
    def __init__(self, df):
        self.df = df

    def exibir(self):
        faturamento = self.df["VL.BRUTO"].sum()
        volume = self.df["QTDE"].sum()
        preco_medio = faturamento / volume if volume else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💰 Faturamento Total", f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        with col2:
            st.metric("📦 Volume Vendido (Caixas)", f"{volume:,.0f}".replace(",", "."))

        with col3:
            st.metric("🏷️ Preço Médio Unitário", f"R$ {preco_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


# Função utilitária fora da classe
def indicador_simples(titulo, valor, col=None):
    if col:
        with col:
            st.metric(label=titulo, value=valor)
    else:
        st.metric(label=titulo, value=valor)
