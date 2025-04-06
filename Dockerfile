# Usar uma imagem base do Python
FROM python:3.11

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar os arquivos do projeto para dentro do container
COPY . /app

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta usada pelo Flask
EXPOSE 5000

# Definir o comando para rodar o app Flask
CMD ["python", "run.py"]
