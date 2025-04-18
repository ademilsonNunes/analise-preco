# Dockerfile para o projeto precos_volume_dashboard
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Copia arquivos de dependências
COPY requirements.txt ./

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante da aplicação
COPY . .

# Exposição da porta padrão do Streamlit
EXPOSE 8501

# Comando para iniciar a aplicação
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.enableCORS=false"]