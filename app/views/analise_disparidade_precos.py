import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from data.processor import Agrupador
from layout.cards import indicador_simples
from layout.filters import FiltroDinamico

# Funções utilitárias para formatação
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_quantity(value):
    return f"{value:,.0f}".replace(",", ".")


def run(df: pd.DataFrame):
    st.subheader("📊 Análise Gerencial de Disparidade de Preço entre Clientes de Perfis Semelhantes")

    with st.expander("🧠 Metodologia e Lógica de Cálculo da Análise", expanded=False):
        st.markdown("""
        Esta análise compara o preço unitário de venda por produto com a média praticada por clientes com perfil similar,
        definido a partir do volume de caixas adquiridas (QTDE) e/ou faturamento (VL.BRUTO).

        O **Índice de Alinhamento de Preço (IAP_CLUSTER)** é calculado dividindo o preço unitário praticado pelo preço médio do grupo:
        `IAP_CLUSTER = PRECO_UNIT / PRECO_CLUSTER_MEDIA`

        ### Classificação com Ícones:
        - 🔴 **Oportunidade (-)** (< 0.85): Preço muito abaixo do padrão  
        - 🟠 **Abaixo da Média** (0.85 – 0.95): Leve desalinhamento  
        - 🟡 **Alinhado** (0.95 – 1.05): Dentro da faixa de equilíbrio  
        - 🟢 **Acima da Média** (1.05 – 1.15): Leve ganho de margem  
        - ⚪ **Oportunidade (+)** (> 1.15): Preço muito acima da média do perfil

        ### Definição das Faixas:
        As faixas dividem os clientes em grupos com base na distribuição de volume (QTDE) e/ou faturamento (VL.BRUTO). 
        Por padrão, são usadas 4 faixas automáticas (quantis), cada uma representando 25% dos dados, identificadas por intervalos (ex.: '1-10 caixas', 'R$ 500,00-R$ 1.500,00'). 
        O número de faixas (2 a 6) pode ser ajustado, e os limites podem ser personalizados manualmente ou selecionados a partir de opções predefinidas (ex.: 'Baixo: 0-50 caixas, Médio: 51-100 caixas'). 
        Uma validação alerta se alguma faixa tiver menos de 5% dos registros, sugerindo ajustes.
        """)

    # Exibir filtros dinâmicos e obter valores
    filtro_dinamico = FiltroDinamico(df)
    filtros = filtro_dinamico.exibir_filtros()

    # Depuração: Verificar o estado do DataFrame inicial
    st.sidebar.markdown(f"**Registros iniciais:** {len(df)}")

    # Aplicar filtros usando Agrupador
    processor = Agrupador(df)
    df_filtrado = processor.filtrar(filtros)

    # Depuração: Verificar após aplicação dos filtros
    st.sidebar.markdown(f"**Registros após filtros:** {len(df_filtrado)}")
    if len(df_filtrado) == 0:
        st.sidebar.markdown("**Filtros Aplicados:**")
        for campo, valor in filtros.items():
            st.sidebar.markdown(f"- {campo}: {valor}")
        st.sidebar.markdown("**Valores Únicos no DataFrame Inicial:**")
        for col in ["SUPERVISOR", "VENDEDOR", "CLIENTE", "DESC", "COD.PRD", "REDE", "NATUREZA"]:
            if col in df.columns:
                valores = sorted([x for x in df[col].dropna().unique() if x])
                st.sidebar.markdown(f"- {col}: {', '.join(map(str, valores))}")

    # Filtro manual para remover cliente padrão
    clientes_antes = len(df_filtrado)
    df_filtrado = df_filtrado[df_filtrado["CLIENTE"] != "CLIENTE PADRAO-000001"]
    clientes_removidos = clientes_antes - len(df_filtrado)

    # Depuração: Verificar após filtro de cliente
    st.sidebar.markdown(f"**Registros após remover cliente padrão:** {len(df_filtrado)}")
    if clientes_removidos > 0:
        st.sidebar.markdown(f"**Clientes removidos (CLIENTE PADRAO-000001):** {clientes_removidos}")

    # Verificar se o DataFrame está vazio
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        st.markdown("**Dica:** Verifique os filtros aplicados na sidebar. Tente ajustar os filtros de 'Natureza', 'Cliente', 'Produto', ou outros para incluir mais dados.")
        return
    
    # Configurações de clusterização
    st.markdown("### ⚙️ Configurações de Clusterização")
    st.markdown("*Os valores padrão (agrupamento por 'Ambos' e 4 faixas) são usados automaticamente, mas podem ser ajustados abaixo.*")
    cluster_by = st.selectbox("Agrupar por", ["Volume (QTDE)", "Faturamento (VL.BRUTO)", "Ambos"], index=2)
    n_quantiles = st.slider("Número de faixas (quantis)", 2, 6, 4)

    # Opção para personalizar limites
    customize_limits = st.checkbox("Personalizar limites das faixas", value=False)
    labels_qtde, labels_vlbruto, qtde_bins, vlbruto_bins = [], [], [], []

    # Definir limites predefinidos
    predefined_options = {
        "QTDE": {
            "3 faixas": {
                "name": "Baixo: 0-50 caixas, Médio: 51-100 caixas, Alto: 101+ caixas",
                "bins": [0, 50, 100, float("inf")],
                "n_quantiles": 3
            },
            "4 faixas": {
                "name": "Muito Baixo: 0-25 caixas, Baixo: 26-50 caixas, Médio: 51-100 caixas, Alto: 101+ caixas",
                "bins": [0, 25, 50, 100, float("inf")],
                "n_quantiles": 4
            }
        },
        "VL.BRUTO": {
            "3 faixas": {
                "name": "Baixo: R$ 0-R$ 1.000, Médio: R$ 1.001-R$ 5.000, Alto: R$ 5.001+",
                "bins": [0, 1000, 5000, float("inf")],
                "n_quantiles": 3
            },
            "4 faixas": {
                "name": "Muito Baixo: R$ 0-R$ 500, Baixo: R$ 501-R$ 1.500, Médio: R$ 1.501-R$ 5.000, Alto: R$ 5.001+",
                "bins": [0, 500, 1500, 5000, float("inf")],
                "n_quantiles": 4
            }
        }
    }

    try:
        if customize_limits:
            # Seleção de limites predefinidos
            if cluster_by in ["Volume (QTDE)", "Ambos"]:
                qtde_min, qtde_max = df_filtrado["QTDE"].min(), df_filtrado["QTDE"].max()
                st.markdown(f"**Intervalo de QTDE**: {format_quantity(qtde_min)} a {format_quantity(qtde_max)}")
                qtde_predefined = st.selectbox(
                    "Escolher limites predefinidos para QTDE",
                    options=["Nenhum"] + [v["name"] for v in predefined_options["QTDE"].values()],
                    key="qtde_predefined"
                )
                if qtde_predefined != "Nenhum":
                    for key, value in predefined_options["QTDE"].items():
                        if value["name"] == qtde_predefined:
                            qtde_bins = value["bins"]
                            n_quantiles = value["n_quantiles"]
                            break
                    # Ajustar bins para cobrir o intervalo real
                    qtde_bins = [qtde_min] + qtde_bins[1:-1] + [qtde_max]
                else:
                    # Inputs manuais
                    qtde_bins = [qtde_min]
                    st.markdown("Defina os limites intermediários para QTDE (valores crescentes):")
                    default_limits = pd.qcut(df_filtrado["QTDE"], q=n_quantiles, retbins=True)[1][1:-1]
                    for i in range(n_quantiles - 1):
                        default = default_limits[i] if i < len(default_limits) else qtde_min + (qtde_max - qtde_min) * (i + 1) / n_quantiles
                        limit = st.number_input(
                            f"Limite {i+1} para QTDE",
                            min_value=float(qtde_min),
                            max_value=float(qtde_max),
                            value=float(default),
                            step=10.0,
                            key=f"qtde_limit_{i}"
                        )
                        qtde_bins.append(limit)
                    qtde_bins.append(qtde_max)
                # Validar limites
                if len(set(qtde_bins)) != len(qtde_bins) or not all(qtde_bins[i] < qtde_bins[i+1] for i in range(len(qtde_bins)-1)):
                    st.error("Erro: Limites de QTDE devem ser únicos e crescentes.")
                    return
                labels_qtde = [f"{format_quantity(qtde_bins[i])}-{format_quantity(qtde_bins[i+1])} caixas" for i in range(len(qtde_bins)-1)]
                df_filtrado["FAIXA_VOLUMETRICA"] = pd.cut(df_filtrado["QTDE"], bins=qtde_bins, labels=labels_qtde, include_lowest=True)
                # Validação avançada
                counts = df_filtrado["FAIXA_VOLUMETRICA"].value_counts()
                total_records = len(df_filtrado)
                for faixa, count in counts.items():
                    if count / total_records < 0.05:
                        st.warning(f"A faixa '{faixa}' tem apenas {count} registros ({count/total_records*100:.1f}%). Considere ajustar os limites ou usar faixas automáticas.")

            if cluster_by in ["Faturamento (VL.BRUTO)", "Ambos"]:
                vlbruto_min, vlbruto_max = df_filtrado["VL.BRUTO"].min(), df_filtrado["VL.BRUTO"].max()
                st.markdown(f"**Intervalo de VL.BRUTO**: {format_currency(vlbruto_min)} a {format_currency(vlbruto_max)}")
                vlbruto_predefined = st.selectbox(
                    "Escolher limites predefinidos para VL.BRUTO",
                    options=["Nenhum"] + [v["name"] for v in predefined_options["VL.BRUTO"].values()],
                    key="vlbruto_predefined"
                )
                if vlbruto_predefined != "Nenhum":
                    for key, value in predefined_options["VL.BRUTO"].items():
                        if value["name"] == vlbruto_predefined:
                            vlbruto_bins = value["bins"]
                            n_quantiles = value["n_quantiles"]
                            break
                    vlbruto_bins = [vlbruto_min] + vlbruto_bins[1:-1] + [vlbruto_max]
                else:
                    vlbruto_bins = [vlbruto_min]
                    st.markdown("Defina os limites intermediários para VL.BRUTO (valores crescentes):")
                    default_limits = pd.qcut(df_filtrado["VL.BRUTO"], q=n_quantiles, retbins=True)[1][1:-1]
                    for i in range(n_quantiles - 1):
                        default = default_limits[i] if i < len(default_limits) else vlbruto_min + (vlbruto_max - vlbruto_min) * (i + 1) / n_quantiles
                        limit = st.number_input(
                            f"Limite {i+1} para VL.BRUTO",
                            min_value=float(vlbruto_min),
                            max_value=float(vlbruto_max),
                            value=float(default),
                            step=500.0,
                            key=f"vlbruto_limit_{i}"
                        )
                        vlbruto_bins.append(limit)
                    vlbruto_bins.append(vlbruto_max)
                # Validar limites
                if len(set(vlbruto_bins)) != len(vlbruto_bins) or not all(vlbruto_bins[i] < vlbruto_bins[i+1] for i in range(len(vlbruto_bins)-1)):
                    st.error("Erro: Limites de VL.BRUTO devem ser únicos e crescentes.")
                    return
                labels_vlbruto = [f"{format_currency(vlbruto_bins[i])}-{format_currency(vlbruto_bins[i+1])}" for i in range(len(vlbruto_bins)-1)]
                df_filtrado["FAIXA_FATURAMENTO"] = pd.cut(df_filtrado["VL.BRUTO"], bins=vlbruto_bins, labels=labels_vlbruto, include_lowest=True)
                # Validação avançada
                counts = df_filtrado["FAIXA_FATURAMENTO"].value_counts()
                total_records = len(df_filtrado)
                for faixa, count in counts.items():
                    if count / total_records < 0.05:
                        st.warning(f"A faixa '{faixa}' tem apenas {count} registros ({count/total_records*100:.1f}%). Considere ajustar os limites ou usar faixas automáticas.")
        else:
            # Clusterização padrão com quantis
            if cluster_by in ["Volume (QTDE)", "Ambos"]:
                qtde_bins = pd.qcut(df_filtrado["QTDE"], q=n_quantiles, retbins=True)[1]
                labels_qtde = [f"{format_quantity(qtde_bins[i])}-{format_quantity(qtde_bins[i+1])} caixas" for i in range(len(qtde_bins)-1)]
                df_filtrado["FAIXA_VOLUMETRICA"] = pd.qcut(df_filtrado["QTDE"], q=n_quantiles, labels=labels_qtde)
            if cluster_by in ["Faturamento (VL.BRUTO)", "Ambos"]:
                vlbruto_bins = pd.qcut(df_filtrado["VL.BRUTO"], q=n_quantiles, retbins=True)[1]
                labels_vlbruto = [f"{format_currency(vlbruto_bins[i])}-{format_currency(vlbruto_bins[i+1])}" for i in range(len(vlbruto_bins)-1)]
                df_filtrado["FAIXA_FATURAMENTO"] = pd.qcut(df_filtrado["VL.BRUTO"], q=n_quantiles, labels=labels_vlbruto)

        # Definir PERFIL_CLIENTE
        if cluster_by == "Volume (QTDE)":
            df_filtrado["PERFIL_CLIENTE"] = df_filtrado["FAIXA_VOLUMETRICA"].astype(str)
        elif cluster_by == "Faturamento (VL.BRUTO)":
            df_filtrado["PERFIL_CLIENTE"] = df_filtrado["FAIXA_FATURAMENTO"].astype(str)
        else:  # Ambos
            df_filtrado["PERFIL_CLIENTE"] = (
                df_filtrado["FAIXA_VOLUMETRICA"].astype(str) + ", " + 
                df_filtrado["FAIXA_FATURAMENTO"].astype(str)
            )
    except ValueError as e:
        st.error(f"Erro na clusterização: {str(e)}. Verifique os limites ou a distribuição dos dados.")
        return

    # Tabela opcional com limites das faixas
    if st.checkbox("Exibir limites das faixas"):
        st.markdown("#### Limites das Faixas")
        limites = []
        if cluster_by in ["Volume (QTDE)", "Ambos"]:
            for i, label in enumerate(labels_qtde):
                min_val = qtde_bins[i]
                max_val = qtde_bins[i+1]
                limites.append({"Faixa": label, "Mínimo": format_quantity(min_val), "Máximo": format_quantity(max_val)})
        if cluster_by in ["Faturamento (VL.BRUTO)", "Ambos"]:
            for i, label in enumerate(labels_vlbruto):
                min_val = vlbruto_bins[i]
                max_val = vlbruto_bins[i+1]
                limites.append({"Faixa": label, "Mínimo": format_currency(min_val), "Máximo": format_currency(max_val)})
        df_limites = pd.DataFrame(limites)
        st.dataframe(df_limites, use_container_width=True)

    media_cluster = df_filtrado.groupby(["COD.PRD", "PERFIL_CLIENTE"])["PRECO_UNIT"].mean().reset_index()
    media_cluster.rename(columns={"PRECO_UNIT": "PRECO_CLUSTER_MEDIA"}, inplace=True)
    df_join = df_filtrado.merge(media_cluster, on=["COD.PRD", "PERFIL_CLIENTE"], how="left")

    # Verificar preços médios inválidos
    if df_join["PRECO_CLUSTER_MEDIA"].isna().any() or (df_join["PRECO_CLUSTER_MEDIA"] == 0).any():
        st.error("Erro: Preços médios nulos ou zero encontrados. Verifique os dados ou filtros aplicados.")
        return

    df_join["IAP_CLUSTER"] = df_join["PRECO_UNIT"] / df_join["PRECO_CLUSTER_MEDIA"]
    df_join["STATUS"] = pd.cut(
        df_join["IAP_CLUSTER"],
        bins=[0, 0.85, 0.95, 1.05, 1.15, np.inf],
        labels=["Oportunidade (-)", "Abaixo da Média", "Alinhado", "Acima da Média", "Oportunidade (+)"]
    )

    # Ícones por status
    icones = {
        "Oportunidade (-)": "🔴",
        "Abaixo da Média": "🟠",
        "Alinhado": "🟡",
        "Acima da Média": "🟢",
        "Oportunidade (+)": "⚪"
    }
    df_join["STATUS_ICON"] = df_join["STATUS"].astype(str).map(icones) + " " + df_join["STATUS"].astype(str)

    # Indicadores
    total_analise = len(df_join)
    abaixo_media = (df_join["STATUS"] == "Oportunidade (-)").sum()
    acima_media = (df_join["STATUS"] == "Oportunidade (+)").sum()

    # Tabelas por perfil
    st.markdown("### 📋 Tabelas por Cluster de Perfil de Cliente")
    for perfil in df_join["PERFIL_CLIENTE"].unique():
        st.markdown(f"#### 📌 Perfil: {perfil}")
        columns = ["CLIENTE", "VENDEDOR", "DESC", "QTDE", "VL.BRUTO", "FAIXA_FATURAMENTO", "PRECO_UNIT", "PRECO_CLUSTER_MEDIA", "IAP_CLUSTER", "STATUS_ICON"] if has_vendedor else ["CLIENTE", "DESC", "QTDE", "VL.BRUTO", "FAIXA_FATURAMENTO", "PRECO_UNIT", "PRECO_CLUSTER_MEDIA", "IAP_CLUSTER", "STATUS_ICON"]
        df_perf = df_join[df_join["PERFIL_CLIENTE"] == perfil][columns].sort_values("IAP_CLUSTER")

        df_perf["VL.BRUTO"] = df_perf["VL.BRUTO"].apply(format_currency)
        df_perf["PRECO_UNIT"] = df_perf["PRECO_UNIT"].apply(format_currency)
        df_perf["PRECO_CLUSTER_MEDIA"] = df_perf["PRECO_CLUSTER_MEDIA"].apply(format_currency)
        df_perf["QTDE"] = df_perf["QTDE"].apply(format_quantity)

        st.dataframe(df_perf, use_container_width=True)

    # Tabela consolidada com filtro por status
    st.markdown("### 📊 Tabela Consolidada por Perfil e Status")
    selected_status = st.session_state.get("selected_status", None)
    consolidado = df_join.groupby(["PERFIL_CLIENTE", "STATUS"]).agg({
        "QTDE": "sum",
        "VL.BRUTO": "sum",
        "PRECO_UNIT": lambda x: np.average(x, weights=df_join.loc[x.index, "QTDE"]),
        "IAP_CLUSTER": lambda x: np.average(x, weights=df_join.loc[x.index, "QTDE"])
    }).reset_index()

    consolidado["QTDE"] = consolidado["QTDE"].apply(format_quantity)
    consolidado["VL.BRUTO"] = consolidado["VL.BRUTO"].apply(format_currency)
    consolidado["PRECO_UNIT"] = consolidado["PRECO_UNIT"].apply(format_currency)
    consolidado["IAP_CLUSTER"] = consolidado["IAP_CLUSTER"].apply(lambda x: f"{x:.2f}".replace(".", ","))

    if selected_status:
        consolidado = consolidado[consolidado["STATUS"] == selected_status]
        st.write(f"Filtrando por status: {selected_status}")

    st.dataframe(consolidado, use_container_width=True)

    # Insights automatizados
    st.markdown("### 💡 Insights Automatizados")
    n_insights = st.slider("Número de insights por categoria", 1, 10, 5)
    st.markdown(f"#### Top {n_insights} Clientes com Menor IAP (Oportunidade de Aumento de Preço)")
    columns_insights = ["CLIENTE", "VENDEDOR", "DESC", "PRECO_UNIT", "PRECO_CLUSTER_MEDIA", "IAP_CLUSTER", "STATUS"] if has_vendedor else ["CLIENTE", "DESC", "PRECO_UNIT", "PRECO_CLUSTER_MEDIA", "IAP_CLUSTER", "STATUS"]
    lowest_iap = df_join.nsmallest(n_insights, "IAP_CLUSTER")[columns_insights]
    lowest_iap["PRECO_UNIT"] = lowest_iap["PRECO_UNIT"].apply(format_currency)
    lowest_iap["PRECO_CLUSTER_MEDIA"] = lowest_iap["PRECO_CLUSTER_MEDIA"].apply(format_currency)
    lowest_iap["IAP_CLUSTER"] = lowest_iap["IAP_CLUSTER"].apply(lambda x: f"{x:.2f}".replace(".", ","))
    st.dataframe(lowest_iap, use_container_width=True)

    st.markdown(f"#### Top {n_insights} Clientes com Maior IAP (Oportunidade de Ajuste de Preço)")
    highest_iap = df_join.nlargest(n_insights, "IAP_CLUSTER")[columns_insights]
    highest_iap["PRECO_UNIT"] = highest_iap["PRECO_UNIT"].apply(format_currency)
    highest_iap["PRECO_CLUSTER_MEDIA"] = highest_iap["PRECO_CLUSTER_MEDIA"].apply(format_currency)
    highest_iap["IAP_CLUSTER"] = highest_iap["IAP_CLUSTER"].apply(lambda x: f"{x:.2f}".replace(".", ","))
    st.dataframe(highest_iap, use_container_width=True)

    # Gráficos
    st.markdown("### 📈 Gráficos Complementares")
    
    # Boxplot com tooltips
    fig1 = px.box(
        df_join,
        x="PERFIL_CLIENTE",
        y="PRECO_UNIT",
        color="STATUS",
        title="Boxplot de Preço Unitário por Perfil",
        hover_data=["CLIENTE", "DESC", "IAP_CLUSTER"]
    )
    fig1.update_traces(
        hovertemplate=(
            "<b>Cliente</b>: %{customdata[0]}<br>" +
            "<b>Produto</b>: %{customdata[1]}<br>" +
            "<b>Preço Unitário</b>: R$ %{y:,.2f}<br>" +
            "<b>IAP</b>: %{customdata[2]:.2f}<br>" +
            "<extra></extra>"
        )
    )
    fig1.update_layout(xaxis_tickangle=45)
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico de barras com interatividade
    df_clientes_unicos = df_join.drop_duplicates(subset=["CLIENTE"])
    bar_data = df_clientes_unicos.groupby("STATUS")["CLIENTE"].nunique().reset_index()
    fig2 = px.bar(
        bar_data,
        x="STATUS",
        y="CLIENTE",
        text_auto=True,
        title="Clientes Únicos por Faixa de Status"
    )
    fig2.update_traces(
        hovertemplate="<b>Status</b>: %{x}<br><b>Clientes Únicos</b>: %{y}<br><extra></extra>",
        marker=dict(opacity=0.8)
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Filtro por clique no gráfico de barras
    if st.button("Limpar filtro de status"):
        st.session_state["selected_status"] = None
    st.markdown("*Clique nas barras acima para filtrar a tabela consolidada por status.*")

    # Gráfico de pizza para proporção de faturamento
    pie_data = df_join.groupby("STATUS")["VL.BRUTO"].sum().reset_index()
    fig_pie = px.pie(
        pie_data,
        names="STATUS",
        values="VL.BRUTO",
        title="Proporção de Faturamento por Status"
    )
    fig_pie.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>Status</b>: %{label}<br><b>Faturamento</b>: R$ %{value:,.2f}<br><b>Proporção</b>: %{percent}<br><extra></extra>"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Histograma com bins ajustáveis
    bins = st.slider("Número de bins no histograma", 10, 100, 50)
    fig3 = px.histogram(
        df_join,
        x="IAP_CLUSTER",
        nbins=bins,
        color="STATUS",
        title="Distribuição do IAP (Índice de Alinhamento)",
        hover_data=["CLIENTE", "DESC", "PRECO_UNIT"]
    )
    fig3.update_traces(
        hovertemplate=(
            "<b>Cliente</b>: %{customdata[0]}<br>" +
            "<b>Produto</b>: %{customdata[1]}<br>" +
            "<b>Preço Unitário</b>: R$ %{customdata[2]:,.2f}<br>" +
            "<b>IAP</b>: %{x:.2f}<br>" +
            "<extra></extra>"
        )
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Histogramas para distribuição de faixas
    st.markdown("### 📊 Distribuição das Faixas de Clusterização")
    if cluster_by in ["Volume (QTDE)", "Ambos"]:
        fig_qtde = px.histogram(
            df_filtrado,
            x="QTDE",
            color="FAIXA_VOLUMETRICA",
            title="Distribuição de QTDE por Faixa Volumétrica",
            nbins=bins
        )
        fig_qtde.update_traces(
            hovertemplate=(
                "<b>Faixa</b>: %{customdata}<br>" +
                "<b>Quantidade</b>: %{x}<br>" +
                "<b>Contagem</b>: %{y}<br>" +
                "<extra></extra>"
            ),
            customdata=df_filtrado["FAIXA_VOLUMETRICA"]
        )
        fig_qtde.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_qtde, use_container_width=True)

    if cluster_by in ["Faturamento (VL.BRUTO)", "Ambos"]:
        fig_vlbruto = px.histogram(
            df_filtrado,
            x="VL.BRUTO",
            color="FAIXA_FATURAMENTO",
            title="Distribuição de VL.BRUTO por Faixa de Faturamento",
            nbins=bins
        )
        fig_vlbruto.update_traces(
            hovertemplate=(
                "<b>Faixa</b>: %{customdata}<br>" +
                "<b>Faturamento</b>: R$ %{x:,.2f}<br>" +
                "<b>Contagem</b>: %{y}<br>" +
                "<extra></extra>"
            ),
            customdata=df_filtrado["FAIXA_FATURAMENTO"]
        )
        fig_vlbruto.update_layout(xaxis_tickformat=",.2f", xaxis_tickangle=45)
        st.plotly_chart(fig_vlbruto, use_container_width=True)

    st.success("✅ Análise validada e ajustada com base na lógica correta de clientes, clusters e indicadores.")