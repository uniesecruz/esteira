# Car Price Prediction - PySpark ML Pipeline

Projeto de Machine Learning para previsão de preços de carros usando **PySpark** com **Regressão Linear**, com execução no **Databricks** e pipeline DevSecOps completo com **Jenkins**, **SonarQube** e **Fortify**.

## Estrutura do Projeto

```
├── .github/workflows/
│   └── ci.yml                        # Pipeline CI/CD (GitHub Actions)
├── databricks/
│   ├── config.py                     # Configuração do Databricks (env vars)
│   └── notebook_pipeline.py          # Notebook Databricks com pipeline ML
├── docker/
│   ├── jenkins/
│   │   ├── Dockerfile                # Jenkins com Python, Databricks CLI
│   │   ├── casc.yaml                 # Jenkins Configuration as Code
│   │   └── plugins.txt               # Plugins Jenkins
│   ├── fortify/
│   │   ├── Dockerfile                # Fortify SCA container
│   │   └── fortify-scan.sh           # Script de scan (fallback: Bandit)
│   └── sonarqube/                    # SonarQube (via Docker image)
├── scripts/
│   ├── deploy_to_databricks.py       # Deploy automatizado ao Databricks
│   └── run_databricks_job.py         # Trigger e monitoramento de jobs
├── src/
│   ├── __init__.py
│   ├── pipeline.py                   # Pipeline ML (local)
│   └── main.py                       # Script de execução local
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py              # 17 testes unitários (pytest)
├── data/
│   └── cars.csv                      # Dataset de carros (50 registros)
├── docker-compose.yml                # Orquestração: Jenkins + SonarQube + Fortify
├── Jenkinsfile                       # Pipeline Jenkins CI/CD
├── sonar-project.properties          # Configuração SonarQube
├── requirements.txt
├── setup.cfg
├── .env.example                      # Template de variáveis de ambiente
└── README.md
```

## Pré-requisitos

- Python 3.9+
- Java 11 ou 17 (para PySpark local)
- Docker e Docker Compose (para Jenkins/SonarQube/Fortify)
- Conta Databricks com token de acesso

## Configuração

### 1. Variáveis de Ambiente

```bash
cp .env.example .env
# Editar .env com suas credenciais:
# - DATABRICKS_HOST
# - DATABRICKS_TOKEN
# - SONAR_TOKEN (após configurar SonarQube)
```

### 2. Instalação Local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Execução Local

```bash
python -m src.main
# ou com caminho customizado:
python -m src.main --data-path /caminho/para/dados.csv
```

## Databricks

### Deploy ao Databricks

O script de deploy:
1. Cria o schema `workspace.esteira` no Unity Catalog
2. Cria o volume `workspace.esteira.data` para armazenamento
3. Faz upload do CSV para o volume
4. Importa o notebook para `/Shared/esteira/`
5. Cria/atualiza o job no Databricks

```bash
export DATABRICKS_HOST="https://dbc-xxxx.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi_seu_token"

python scripts/deploy_to_databricks.py
```

### Executar Job no Databricks

```bash
python scripts/run_databricks_job.py
```

### Notebook

O notebook está disponível em:
`/Shared/esteira/car_price_prediction`

Dados armazenados em:
`/Volumes/workspace/esteira/data/cars.csv`

## Docker - DevSecOps Stack

### Subir todos os serviços

```bash
# Configurar variáveis
export DATABRICKS_HOST="https://dbc-xxxx.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi_seu_token"

# Subir Jenkins + SonarQube
docker compose up -d

# Acessar:
# Jenkins:   http://localhost:8080 (admin/admin)
# SonarQube: http://localhost:9000 (admin/admin)
```

### Executar scan SonarQube

```bash
# Após configurar o token no SonarQube:
export SONAR_TOKEN="seu_token_sonarqube"
docker compose run --rm sonar-scanner
```

### Executar scan Fortify / Bandit

```bash
# Usa Bandit como fallback se Fortify não estiver instalado
docker compose --profile fortify run --rm fortify
```

### Parar serviços

```bash
docker compose down
```

## Testes

```bash
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Qualidade de Código

```bash
flake8 src/ tests/ --max-line-length 100
black --check --line-length 100 src/ tests/
bandit -r src/ --severity-level medium
```

## Pipeline CI/CD

### GitHub Actions
Executado automaticamente em `push` e `pull_request` para `main`:
1. **Lint** - flake8 + black
2. **Segurança** - bandit
3. **Testes** - pytest com cobertura

### Jenkins
Pipeline completo com:
1. Lint (flake8 + black)
2. Segurança (bandit)
3. SonarQube Analysis
4. Quality Gate
5. Testes com cobertura
6. Fortify (opcional)
7. Deploy ao Databricks (branch main)
8. Execução do Job no Databricks

## Métricas do Modelo

- **RMSE** (Root Mean Squared Error)
- **R²** (R-squared)
