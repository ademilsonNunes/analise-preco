import streamlit as st
from data.loader import carregar_dados
from layout.filters import FiltroDinamico
from views import (
    resumo_executivo,
    analise_produto,
    analise_cliente,
    analise_rede,
    analise_vendedor,
    analise_verba,
    analise_bonificacoes,
    analise_contratos,
    positivacao_clientes,
    analise_devolucoes,
    analise_disparidade_precos
)

# Configuração de página
st.set_page_config(page_title="Dashboard - Gestão Comercial", layout="wide")

# Estilo CSS
with open("app/assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Título principal
st.title("📊 Dashboard - Gestão Comercial")
st.markdown("Acompanhe a performance mensal por cliente, produto, rede, vendedor e supervisor.")

# Menu lateral
st.sidebar.title("📌 Navegação")
pagina = st.sidebar.selectbox("Selecione a Página", [
    "Resumo Executivo",
    "Análise por Produto",
    "Análise por Cliente",
    "Análise por Rede",
    "Análise por Vendedor",
    "Análise de Devoluções",
    "Análise de Contratos",
    "Análise de Verbas",
    "Análise de Bonificações",
    "Análise de Disparidade de Preços",
    "Positivação de Clientes"
])

# Carregar dados
try:
    df = carregar_dados()
except Exception as e:
    st.error(f"⚠️ Erro ao carregar dados: {str(e)}")
    st.stop()

# Filtros
filtros = FiltroDinamico(df).exibir_filtros()
st.session_state["filtros"] = filtros

# Roteamento
if pagina == "Resumo Executivo":
    dashboard = resumo_executivo.Dashboard(df)
    dashboard.run()
elif pagina == "Análise por Produto":
    analise_produto.run(df)
elif pagina == "Análise por Cliente":
    analise_cliente.run(df)
elif pagina == "Análise por Rede":
    analise_rede.run(df)
elif pagina == "Análise por Vendedor":
    analise_vendedor.run(df)
elif pagina == "Positivação de Clientes":
    positivacao_clientes.run(df)
elif pagina == "Análise de Bonificações":
    analise_bonificacoes.run(df)    
elif pagina == "Análise de Devoluções":
    analise_devolucoes.run(df)    
elif pagina == "Análise de Verbas":
    analise_verba.run(df)
elif pagina == "Análise de Contratos":
    analise_contratos.run(df)    
elif pagina == "Análise de Disparidade de Preços":     
    analise_disparidade_precos.run(df)