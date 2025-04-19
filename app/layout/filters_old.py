# app/layout/filters.py

import streamlit as st
import pandas as pd

class FiltroDinamico:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        # Criar mapeamento Supervisor -> Vendedores
        self.supervisor_vendedores = self.df.groupby('SUPERVISOR')['VENDEDOR'].unique().apply(list).to_dict()
        # Tratar nulos
        self.supervisor_vendedores = {k: v for k, v in self.supervisor_vendedores.items() if pd.notnull(k)}
        for k in self.supervisor_vendedores:
            self.supervisor_vendedores[k] = [v for v in self.supervisor_vendedores[k] if pd.notnull(v)]

    def exibir_filtros(self):
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

            # Botão para limpar filtros
            if st.button("🗑️ Limpar Filtros", key="limpar_filtros_button"):
                for key in ["filtro_supervisor", "filtro_vendedor", "filtro_cliente", "filtro_produto", "filtro_sku", "filtro_rede", "filtro_natureza"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

            # Supervisor
            st.markdown('<p class="filter-label">👨‍💼 Supervisor</p>', unsafe_allow_html=True)
            supervisores = ["Todos"] + sorted([x for x in self.df["SUPERVISOR"].dropna().unique() if x])
            supervisor = st.selectbox(
                "",
                supervisores,
                key="filtro_supervisor",
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
            
            vendedor = st.multiselect(
                "",
                ["Todos"] + vendedores,
                default=vendedor_default,
                key="filtro_vendedor"
            )
            
            # Cliente
            st.markdown('<p class="filter-label">👥 Cliente</p>', unsafe_allow_html=True)
            clientes = ["Todos"] + sorted([x for x in self.df["CLIENTE"].dropna().unique() if x])
            cliente = st.multiselect(
                "",
                clientes,
                default=["Todos"],
                key="filtro_cliente"
            )

            # Produto
            st.markdown('<p class="filter-label">🧼 Produto</p>', unsafe_allow_html=True)
            produtos = ["Todos"] + sorted([x for x in self.df["DESC"].dropna().unique() if x])
            produto = st.multiselect(
                "",
                produtos,
                default=["Todos"],
                key="filtro_produto"
            )
            
            # SKU
            st.markdown('<p class="filter-label">🔢 SKU</p>', unsafe_allow_html=True)
            skus = ["Todos"] + sorted([x for x in self.df["COD.PRD"].dropna().unique() if x])
            sku = st.multiselect(
                "",
                skus,
                default=["Todos"],
                key="filtro_sku"
            )
            
            # Rede
            st.markdown('<p class="filter-label">🏪 Rede</p>', unsafe_allow_html=True)
            redes = ["Todos"] + sorted([x for x in self.df["REDE"].dropna().unique() if x])
            rede = st.multiselect(
                "",
                redes,
                default=["Todos"],
                key="filtro_rede"
            )

            # Natureza
            st.markdown('<p class="filter-label">🧾 Tipo de Registro (Natureza)</p>', unsafe_allow_html=True)
            # Depuração: Exibir valores únicos de NATUREZA
            naturezas_unicas = sorted([x for x in self.df["NATUREZA"].dropna().unique() if x])
            st.markdown(f"**Valores disponíveis para Natureza:** {', '.join(naturezas_unicas)}")
            natureza = st.multiselect(
                "",
                naturezas_unicas,
                default=naturezas_unicas,
                key="filtro_natureza"
            )
            # Validação: Garantir que pelo menos uma opção seja selecionada
            if not natureza:
                st.warning("⚠️ Pelo menos um valor de 'Natureza' deve ser selecionado.")
                natureza = naturezas_unicas  # Reverter para o padrão

        # Converter "Todos" para None para facilitar filtragem
        return {
            "SUPERVISOR": None if supervisor == "Todos" else supervisor,
            "REDE": None if "Todos" in rede else rede,
            "VENDEDOR": None if "Todos" in vendedor or "Nenhum" in vendedor else vendedor,
            "CLIENTE": None if "Todos" in cliente else cliente,
            "DESC": None if "Todos" in produto else produto,
            "COD.PRD": None if "Todos" in sku else sku,
            "NATUREZA": natureza
        }
    
    def _reset_vendedor(self):
        """Reseta o filtro de vendedor ao mudar o supervisor."""
        if "filtro_vendedor" in st.session_state:
            st.session_state["filtro_vendedor"] = ["Todos"]