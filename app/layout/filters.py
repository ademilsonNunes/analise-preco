# app/layout/filters.py
import streamlit as st
import pandas as pd
from typing import Dict, List

class FiltroDinamico:
    def __init__(self, df: pd.DataFrame, filter_id: str = "default"):
        """
        Inicializa o gerenciador de filtros dinâmicos com um ID único.

        Args:
            df (pd.DataFrame): DataFrame com os dados a serem filtrados.
            filter_id (str): Identificador único para esta instância de filtros.
        """
        self.df = df
        self.filter_id = filter_id
        # Criar mapeamento Supervisor -> Vendedores
        self.supervisor_vendedores = self.df.groupby('SUPERVISOR')['VENDEDOR'].unique().apply(list).to_dict()
        # Tratar nulos
        self.supervisor_vendedores = {k: v for k, v in self.supervisor_vendedores.items() if pd.notnull(k)}
        for k in self.supervisor_vendedores:
            self.supervisor_vendedores[k] = [v for v in self.supervisor_vendedores[k] if pd.notnull(v)]
        # Inicializar filtros no session_state
        if f"filtros_{filter_id}" not in st.session_state:
            st.session_state[f"filtros_{filter_id}"] = {}

    def exibir_filtros(self) -> Dict[str, any]:
        """
        Exibe os widgets de filtro no Streamlit e retorna os valores selecionados.

        Returns:
            Dict[str, any]: Dicionário com os filtros selecionados.
        """
        with st.sidebar.expander("🔍 Filtros", expanded=True):
            # Estilo para melhorar legibilidade
            st.markdown(
                """
                <style>
                .filter-label { font-weight: bold; margin-bottom: 5px; margin-top: 10px; }
                .stMultiSelect > div > div > div { white-space: normal !important; word-wrap: break-word; }
                .stSelectbox > div > div > div { white-space: normal !important; word-wrap: break-word; }
                </style>
                """,
                unsafe_allow_html=True
            )

            # Supervisor
            st.markdown('<p class="filter-label">👨‍💼 Supervisor</p>', unsafe_allow_html=True)
            supervisores = ["Todos"] + sorted([x for x in self.df["SUPERVISOR"].dropna().unique() if x])
            supervisor_key = f"filtro_supervisor_{self.filter_id}"
            supervisor = st.selectbox(
                "",
                supervisores,
                key=supervisor_key,
                on_change=self._reset_vendedor
            )

            # Vendedor
            st.markdown('<p class="filter-label">🧍‍♂️ Vendedor</p>', unsafe_allow_html=True)
            if supervisor == "Todos" or supervisor not in self.supervisor_vendedores:
                vendedores = sorted([x for x in self.df["VENDEDOR"].dropna().unique() if x])
            else:
                vendedores = sorted(self.supervisor_vendedores.get(supervisor, []))

            if not vendedores:
                st.warning("⚠️ Nenhum vendedor associado ao supervisor selecionado.")
                vendedores = ["Nenhum"]
                vendedor_default = ["Nenhum"]
            else:
                vendedor_default = ["Todos"]

            vendedor_key = f"filtro_vendedor_{self.filter_id}"
            vendedor = st.multiselect(
                "",
                ["Todos"] + vendedores,
                default=vendedor_default,
                key=vendedor_key
            )

            # Cliente
            st.markdown('<p class="filter-label">👥 Cliente</p>', unsafe_allow_html=True)
            clientes = ["Todos"] + sorted([x for x in self.df["CLIENTE"].dropna().unique() if x])
            cliente_key = f"filtro_cliente_{self.filter_id}"
            cliente = st.multiselect(
                "",
                clientes,
                default=["Todos"],
                key=cliente_key
            )

            # Produto
            st.markdown('<p class="filter-label">🧼 Produto</p>', unsafe_allow_html=True)
            produtos = ["Todos"] + sorted([x for x in self.df["DESC"].dropna().unique() if x])
            produto_key = f"filtro_produto_{self.filter_id}"
            produto = st.multiselect(
                "",
                produtos,
                default=["Todos"],
                key=produto_key
            )

            # SKU
            st.markdown('<p class="filter-label">🔢 SKU</p>', unsafe_allow_html=True)
            skus = ["Todos"] + sorted([x for x in self.df["COD.PRD"].dropna().unique() if x])
            sku_key = f"filtro_sku_{self.filter_id}"
            sku = st.multiselect(
                "",
                skus,
                default=["Todos"],
                key=sku_key
            )

            # Rede
            st.markdown('<p class="filter-label">🏪 Rede</p>', unsafe_allow_html=True)
            redes = ["Todos"] + sorted([x for x in self.df["REDE"].dropna().unique() if x])
            rede_key = f"filtro_rede_{self.filter_id}"
            rede = st.multiselect(
                "",
                redes,
                default=["Todos"],
                key=rede_key
            )

            # Natureza
            st.markdown('<p class="filter-label">🧾 Tipo de Registro (Natureza)</p>', unsafe_allow_html=True)
            naturezas_unicas = sorted([x for x in self.df["NATUREZA"].dropna().unique() if x])
            st.markdown(f"**Valores disponíveis para Natureza:** {', '.join(naturezas_unicas)}")
            natureza_key = f"filtro_natureza_{self.filter_id}"
            natureza = st.multiselect(
                "",
                naturezas_unicas,
                default=naturezas_unicas,
                key=natureza_key
            )
            if not natureza:
                st.warning("⚠️ Pelo menos um valor de 'Natureza' deve ser selecionado.")
                natureza = naturezas_unicas

        # Armazenar filtros no session_state
        filtros = {
            "SUPERVISOR": None if supervisor == "Todos" else supervisor,
            "REDE": None if "Todos" in rede else rede,
            "VENDEDOR": None if "Todos" in vendedor or "Nenhum" in vendedor else vendedor,
            "CLIENTE": None if "Todos" in cliente else cliente,
            "DESC": None if "Todos" in produto else produto,
            "COD.PRD": None if "Todos" in sku else sku,
            "NATUREZA": natureza
        }
        st.session_state[f"filtros_{self.filter_id}"] = filtros
        return filtros

    def _reset_vendedor(self):
        """Reseta o filtro de vendedor ao mudar o supervisor."""
        vendedor_key = f"filtro_vendedor_{self.filter_id}"
        if vendedor_key in st.session_state:
            st.session_state[vendedor_key] = ["Todos"]