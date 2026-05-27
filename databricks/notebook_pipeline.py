# Databricks notebook source
# MAGIC %md
# MAGIC # Car Price Prediction - PySpark ML Pipeline
# MAGIC Pipeline de Machine Learning para previsão de preços de carros usando Regressão Linear.
# MAGIC
# MAGIC **Etapas:**
# MAGIC 1. Leitura dos dados (CSV no DBFS)
# MAGIC 2. Limpeza e tratamento
# MAGIC 3. Feature Engineering (VectorAssembler, StringIndexer)
# MAGIC 4. Treino da Regressão Linear
# MAGIC 5. Avaliação (RMSE, R²)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuração e Imports

# COMMAND ----------

from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Leitura dos Dados

# COMMAND ----------

DATA_PATH = "/Volumes/workspace/esteira/data/cars.csv"

raw_df = spark.read.csv(DATA_PATH, header=True, inferSchema=True)  # noqa: F821
print(f"Total de registros: {raw_df.count()}")
raw_df.printSchema()
display(raw_df.limit(10))  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Limpeza e Tratamento dos Dados

# COMMAND ----------


def clean_data(df):
    """Limpa e transforma os dados brutos."""
    df = df.withColumn(
        "mileage",
        F.regexp_extract(F.col("mileage"), r"([\d.]+)", 1).cast(DoubleType()),
    )
    df = df.withColumn(
        "engine",
        F.regexp_extract(F.col("engine"), r"([\d.]+)", 1).cast(DoubleType()),
    )
    df = df.withColumn(
        "max_power",
        F.regexp_extract(F.col("max_power"), r"([\d.]+)", 1).cast(DoubleType()),
    )

    critical_columns = ["year", "selling_price", "km_driven", "mileage", "engine", "max_power"]
    df = df.dropna(subset=critical_columns)

    df = df.withColumn("year", F.col("year").cast(IntegerType()))
    df = df.withColumn("selling_price", F.col("selling_price").cast(IntegerType()))
    df = df.withColumn("km_driven", F.col("km_driven").cast(IntegerType()))
    df = df.withColumn("seats", F.col("seats").cast(IntegerType()))

    return df


cleaned_df = clean_data(raw_df)
print(f"Registros após limpeza: {cleaned_df.count()}")
display(cleaned_df.describe())  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Validação de Qualidade dos Dados

# COMMAND ----------

required_columns = [
    "year",
    "selling_price",
    "km_driven",
    "fuel",
    "seller_type",
    "transmission",
    "owner",
    "mileage",
    "engine",
    "max_power",
    "seats",
]

for col_name in required_columns:
    null_count = cleaned_df.filter(F.col(col_name).isNull()).count()
    if null_count > 0:
        print(f"ALERTA: Coluna '{col_name}' tem {null_count} valores nulos")
    else:
        print(f"OK: Coluna '{col_name}' sem nulos")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Feature Engineering

# COMMAND ----------

categorical_columns = ["fuel", "seller_type", "transmission", "owner"]
indexed_columns = [f"{c}_index" for c in categorical_columns]

indexers = [
    StringIndexer(inputCol=col, outputCol=f"{col}_index", handleInvalid="keep")
    for col in categorical_columns
]

numeric_columns = ["year", "km_driven", "mileage", "engine", "max_power", "seats"]
feature_columns = numeric_columns + indexed_columns

assembler = VectorAssembler(
    inputCols=feature_columns,
    outputCol="features",
    handleInvalid="skip",
)

feature_pipeline = Pipeline(stages=indexers + [assembler])
feature_model = feature_pipeline.fit(cleaned_df)
featured_df = feature_model.transform(cleaned_df)

print(f"Features criadas: {len(feature_columns)} dimensões")
display(featured_df.select("features", "selling_price").limit(5))  # noqa: F821

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Split Treino/Teste e Treinamento do Modelo

# COMMAND ----------

train_df, test_df = featured_df.randomSplit([0.8, 0.2], seed=42)
print(f"Treino: {train_df.count()} registros")
print(f"Teste: {test_df.count()} registros")

lr = LinearRegression(
    featuresCol="features",
    labelCol="selling_price",
    maxIter=100,
    regParam=0.3,
    elasticNetParam=0.8,
)

model = lr.fit(train_df)

print(f"\nCoeficientes: {model.coefficients}")
print(f"Intercepto: {model.intercept}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Avaliação do Modelo

# COMMAND ----------

predictions = model.transform(test_df)

rmse_evaluator = RegressionEvaluator(
    labelCol="selling_price", predictionCol="prediction", metricName="rmse"
)
r2_evaluator = RegressionEvaluator(
    labelCol="selling_price", predictionCol="prediction", metricName="r2"
)

rmse = rmse_evaluator.evaluate(predictions)
r2 = r2_evaluator.evaluate(predictions)

print(f"RMSE: {rmse:,.2f}")
print(f"R² (R-squared): {r2:.4f}")

display(  # noqa: F821
    predictions.select("car_name", "selling_price", "prediction")
    .withColumn("prediction", F.round("prediction", 0))
    .withColumn("error", F.abs(F.col("selling_price") - F.col("prediction")))
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Salvar Modelo no DBFS

# COMMAND ----------

MODEL_PATH = "/Volumes/workspace/esteira/data/models/car_price_lr"
model.write().overwrite().save(MODEL_PATH)
print(f"Modelo salvo em: {MODEL_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Resumo dos Resultados

# COMMAND ----------

print("=" * 60)
print("RESUMO - Car Price Prediction")
print("=" * 60)
print(f"Dataset: {raw_df.count()} registros (bruto) -> {cleaned_df.count()} (limpo)")
print(f"Features: {len(feature_columns)} dimensões")
print(f"Split: {train_df.count()} treino / {test_df.count()} teste")
print(f"RMSE: {rmse:,.2f}")
print(f"R²: {r2:.4f}")
print(f"Modelo: {MODEL_PATH}")
print("=" * 60)
