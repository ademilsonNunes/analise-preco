# 📊 Dashboard de Preço e Volume

Este projeto é um dashboard interativo construído com **Python**, **Streamlit** e **Plotly** para analisar a evolução de preço unitário e volume vendido por produto e cliente ao longo do tempo.

## 🚀 Funcionalidades

- Filtros interativos por **cliente** e **produto**
- Gráficos de **preço unitário** e **volume vendido**
- Tabela com **faturamento** e **quantidades** por período
- Indicadores resumidos com cards visuais

## 📁 Estrutura de Pastas

```bash
app/
├── data/
│   └── loader.py         # Carregamento e tratamento da base
├── layout/
│   ├── filters.py        # Filtros interativos
│   ├── charts.py         # Gráficos principais
│   └── cards.py          # Indicadores resumidos
├── main.py               # App principal (OO)
```

## 📦 Requisitos

- Python 3.9+

### Instalar dependências
```bash
pip install -r requirements.txt
```

### Executar localmente
```bash
streamlit run app/main.py
```

## 🐳 Usando Docker

### Build da imagem
```bash
docker-compose build
```

### Executar a aplicação
```bash
docker-compose up
```

Acesse em: [http://localhost:8501](http://localhost:8501)

## 📄 Dados

- A base de dados utilizada é um arquivo Excel (`dados.slxs.xlsx`) com colunas como `CLIENTE`, `DESC`, `VL.BRUTO`, `QTDE` e `EMISSAO`.
- A coluna `CUSTO_UNIT` é opcional.

## 🧪 Testes

Para rodar os testes (caso incluídos):
```bash
pytest
```
1
---

Desenvolvido para monitorar variações de preço e volume de maneira gerencial. Ideal para equipes comerciais e financeiras.
---

## Comandos docker 

docker login
docker compose up --build
docker images
docker tag analise-preco-dashboard ademilsonnunes/gestao_comercial:latest
docker push ademilsonnunes/gestao_comercial:latest
---

## docker-hub comandos
docker login - u
docker pull ademilsonnunes/gestao_comercial
docker run -d -p 8501:8501 --name gestao_comercial ademilson/gestao_comercial:latest
