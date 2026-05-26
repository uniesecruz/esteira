# Car Price Prediction - PySpark ML Pipeline

Projeto de Machine Learning para previsão de preços de carros usando **PySpark** com **Regressão Linear**, seguindo boas práticas de engenharia de software, testes e CI/CD.

## Estrutura do Projeto

```
├── .github/workflows/
│   └── ci.yml              # Pipeline CI/CD (lint, segurança, testes)
├── data/
│   └── cars.csv             # Dataset de carros
├── src/
│   ├── __init__.py
│   ├── pipeline.py          # Pipeline ML (limpeza, features, treino, avaliação)
│   └── main.py              # Script de execução principal
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py     # Testes unitários com pytest
├── requirements.txt
├── setup.cfg                # Configuração do flake8
└── README.md
```

## Pré-requisitos

- Python 3.9+
- Java 11 ou 17 (necessário para o PySpark)

## Instalação

```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
```

## Executar o Pipeline

```bash
# Usar caminho padrão (data/cars.csv)
python -m src.main

# Especificar caminho do dataset
python -m src.main --data-path /caminho/para/dados.csv

# Ou usar variável de ambiente
export DATA_PATH=/caminho/para/dados.csv
python -m src.main
```

## Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Qualidade de Código

```bash
# Linting
flake8 src/ tests/

# Formatação
black --check src/ tests/

# Segurança
bandit -r src/
```

## Pipeline CI/CD

O GitHub Actions executa automaticamente em `push` e `pull_request` para `main`:

1. **Lint** - flake8 + black (verificação de estilo)
2. **Segurança** - bandit (análise estática de segurança)
3. **Testes** - pytest com cobertura de código

## Métricas do Modelo

O pipeline avalia o modelo usando:
- **RMSE** (Root Mean Squared Error) - erro médio das previsões
- **R²** (R-squared) - proporção da variância explicada pelo modelo
