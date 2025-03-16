# Geo

Aplicação web para segmentação e classificação de imagens de satélite.

## Acessando o projeto
> É necessário ter Python, Docker e Git instalados na sua máquina

Baixe o projeto:
```bash
git clone https://github.com/RaiannyF/geo.git
```

Entre na pasta do projeto e construa a imagem Docker:
```bash
docker build -t geo-app .
```

Rode a aplicação:
```bash
docker run -p 5000:5000 geo-app
```

Agora, basta acessar o link gerado para acessar a interface web.