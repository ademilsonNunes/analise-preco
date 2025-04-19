# 📍 Roadmap Técnico - Dashboard Preço e Volume

## 🔹 Fase 1 – Faturamento (Concluído)

| Tarefa | Status |
|--------|--------|
| Filtros por cliente e produto | ✅ |
| Gráficos de volume e preço unitário | ✅ |
| Cards de indicadores (faturamento, volume, preço médio) | ✅ |
| Dockerfile e README estruturado | ✅ |
| Filtros por supervisor, vendedor e rede |  ✅ |
| Variação mês a mês de volume e preço (Δ%) |  ✅ |
| Exportação dos dados (CSV/Excel) | 🔜 |

---

## 🔸 Fase 2 – Bonificações

| Tarefa | Status |
|--------|--------|
| Separar base com TP in [F3, FC, FJ, FS] |  ✅ |
| Volume mensal de bonificação por cliente/produto |  ✅ |
| Gráficos comparativos com vendas |  ✅ |
| Indicadores % bonificação por cliente/produto |  ✅ |

---

## 🔻 Fase 3 – Devoluções

| Tarefa | Status |
|--------|--------|
| Separar TP in [DS, DJ, D3, DC] |  ✅ |
| Impacto no volume total |  ✅ |
| Principais clientes/produtos com devolução |  ✅ |
| Análise cruzada por vendedor e supervisor |  ✅ |

---

## 🔬 Fase 4 – Recursos Avançados

| Recurso | Status |
|---------|--------|
| Controle de acesso por perfil (admin, vendas, gestor) | 🔜 |
| Geração de relatórios automáticos em PDF | 🔜 |
| Interface mobile ou frontend separado | 🔜 |
| Integração com ERP (via API, dump ou webhook) | 🔜 |

---

Este roadmap serve como guia para as próximas etapas do projeto e deve ser ajustado conforme novas demandas forem surgindo. Para cada fase, é recomendável aplicar testes automatizados e validação com usuários-chave.

# 📌 Roadmap do Projeto — Análise de Preço, Volume e Positivação de Clientes

## 🎯 Objetivo Geral
Desenvolver um painel de controle gerencial (BI) que possibilite a análise temporal de preços unitários, volume de vendas, evolução por cliente, produto, vendedor, rede e supervisor. Além disso, oferecer ferramentas para monitorar positividade de clientes e suporte à tomada de decisão comercial.

---

## ✅ Funcionalidades Concluídas

### 🧱 Infraestrutura
- [x] Estrutura modular com orientação a objetos
- [x] Leitura de dados via Pandas com cache Parquet
- [x] Conversão automática de Excel → Parquet (com hash)

### 🎨 Visual e Layout
- [x] Sidebar personalizada
- [x] Aplicação de CSS customizado
- [x] Menu de navegação entre páginas

### 📊 Páginas implementadas
- [x] Resumo Executivo: indicadores globais, gráficos e evolução de preços unitários
- [x] Análise por Produto (estrutura preparada)
- [x] Análise por Cliente (estrutura preparada)
- [x] Análise por Rede (estrutura preparada)
- [x] Análise de Devoluções (estrutura preparada)
- [x] Positivação de Clientes:
  - [x] Total de clientes ativos por mês
  - [x] Mapa de calor cliente x mês (VL.BRUTO)
  - [x] Novos clientes
  - [x] Inativos
  - [x] Clientes que retornaram
  - [x] Taxa de recompra
  - [x] Gráfico de evolução de clientes ativos

---

## 🛠️ Em Desenvolvimento / Próximos Passos

### 🔍 Métricas Avançadas e Visões de Comparação
- [x] Implementar análise de devoluções com % sobre o faturamento
- [x] Análise de bonificações por cliente/produto
- [x] Adicionar linha de custo médio no gráfico de preço unitário
- [x] Comparativo de preço entre meses (diferença e % variação)
- [x] Exportação de relatórios para Excel/PDF

### 📈 Otimizações
- [x] Refatorar gráficos para mostrar tooltip detalhado
- [x] Adicionar mapa de calor na visão de produto (opcional)
- [x] Ajustar performance para bases muito grandes (parquet particionado)
- [x] Tela de carregamento e indicadores de progresso
- [ ] Permitir seleção multipla em filtros como Produto, SKU e Cliente.
- [ ] Otimizar todos as views, eliminndo informção desnecessária. 
 
---

## 💡 Próximo sprint
- [ ] Análise de Mix Ideal de Produtos
- [ ] Modelo de Previsão com base em séries temporais
- [ ] Integração com banco de dados (substituir planilhas)
- [ ] Controle de permissões por perfil de usuário (admin, comercial, etc)

---

_Última atualização: 15/04/2025 às 08:36_
