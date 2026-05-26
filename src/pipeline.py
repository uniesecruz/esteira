"""
PySpark ML Pipeline for Car Price Prediction.

Modularized pipeline with data loading, cleaning, feature engineering,
model training, and evaluation stages.
"""

import os

from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

EXPECTED_SCHEMA = StructType(
    [
        StructField("car_name", DoubleType(), True),
        StructField("year", IntegerType(), True),
        StructField("selling_price", IntegerType(), True),
        StructField("km_driven", IntegerType(), True),
        StructField("fuel", DoubleType(), True),
        StructField("seller_type", DoubleType(), True),
        StructField("transmission", DoubleType(), True),
        StructField("owner", DoubleType(), True),
        StructField("mileage", DoubleType(), True),
        StructField("engine", DoubleType(), True),
        StructField("max_power", DoubleType(), True),
        StructField("seats", IntegerType(), True),
    ]
)


def get_spark_session(app_name: str = "CarPricePrediction") -> SparkSession:
    """Create or retrieve a SparkSession."""
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )


def load_data(spark: SparkSession, path: str = "") -> DataFrame:
    """
    Load CSV data from the given path.

    If no path is provided, reads from the DATA_PATH environment variable
    or defaults to 'data/cars.csv'.
    """
    if not path:
        path = os.environ.get("DATA_PATH", "data/cars.csv")

    return spark.read.csv(path, header=True, inferSchema=True)


def clean_data(df: DataFrame) -> DataFrame:
    """
    Clean and transform raw car data.

    - Extracts numeric values from mileage, engine, and max_power columns.
    - Drops rows with null values in critical columns.
    - Casts columns to appropriate types.
    """
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

    critical_columns = [
        "year",
        "selling_price",
        "km_driven",
        "mileage",
        "engine",
        "max_power",
    ]
    df = df.dropna(subset=critical_columns)

    df = df.withColumn("year", F.col("year").cast(IntegerType()))
    df = df.withColumn("selling_price", F.col("selling_price").cast(IntegerType()))
    df = df.withColumn("km_driven", F.col("km_driven").cast(IntegerType()))
    df = df.withColumn("seats", F.col("seats").cast(IntegerType()))

    return df


def validate_data(df: DataFrame) -> dict:
    """
    Validate data quality before training.

    Returns a dict with validation results including null counts
    and schema conformity checks.
    """
    total_rows = df.count()
    results = {"total_rows": total_rows, "issues": []}

    if total_rows == 0:
        results["issues"].append("DataFrame is empty")
        return results

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
    existing_columns = df.columns
    missing = [c for c in required_columns if c not in existing_columns]
    if missing:
        results["issues"].append(f"Missing columns: {missing}")

    for col_name in required_columns:
        if col_name in existing_columns:
            null_count = df.filter(F.col(col_name).isNull()).count()
            if null_count > 0:
                results["issues"].append(f"Column '{col_name}' has {null_count} null values")

    return results


def build_feature_pipeline() -> Pipeline:
    """
    Build the feature engineering pipeline.

    Uses StringIndexer for categorical columns and VectorAssembler
    to combine all features into a single vector.
    """
    categorical_columns = ["fuel", "seller_type", "transmission", "owner"]
    indexed_columns = [f"{c}_index" for c in categorical_columns]

    indexers = [
        StringIndexer(
            inputCol=col,
            outputCol=f"{col}_index",
            handleInvalid="keep",
        )
        for col in categorical_columns
    ]

    numeric_columns = ["year", "km_driven", "mileage", "engine", "max_power", "seats"]
    feature_columns = numeric_columns + indexed_columns

    assembler = VectorAssembler(
        inputCols=feature_columns,
        outputCol="features",
        handleInvalid="skip",
    )

    return Pipeline(stages=indexers + [assembler])


def train_model(
    train_df: DataFrame,
    max_iter: int = 100,
    reg_param: float = 0.3,
    elastic_net_param: float = 0.8,
) -> LinearRegression:
    """
    Train a Linear Regression model on the prepared training data.

    Returns the fitted model.
    """
    lr = LinearRegression(
        featuresCol="features",
        labelCol="selling_price",
        maxIter=max_iter,
        regParam=reg_param,
        elasticNetParam=elastic_net_param,
    )
    return lr.fit(train_df)


def evaluate_model(model, test_df: DataFrame) -> dict:
    """
    Evaluate the trained model using RMSE and R-squared metrics.

    Returns a dict with metric names and values.
    """
    predictions = model.transform(test_df)

    rmse_evaluator = RegressionEvaluator(
        labelCol="selling_price",
        predictionCol="prediction",
        metricName="rmse",
    )
    r2_evaluator = RegressionEvaluator(
        labelCol="selling_price",
        predictionCol="prediction",
        metricName="r2",
    )

    rmse = rmse_evaluator.evaluate(predictions)
    r2 = r2_evaluator.evaluate(predictions)

    return {"rmse": rmse, "r2": r2}


def run_pipeline(data_path: str = "") -> dict:
    """
    Execute the full ML pipeline end-to-end.

    Steps:
    1. Load data
    2. Clean data
    3. Validate data quality
    4. Feature engineering
    5. Train/test split
    6. Model training
    7. Evaluation

    Returns a dict with validation results and model metrics.
    """
    spark = get_spark_session()

    raw_df = load_data(spark, data_path)
    cleaned_df = clean_data(raw_df)
    validation = validate_data(cleaned_df)

    if validation["issues"]:
        print(f"Data quality warnings: {validation['issues']}")

    feature_pipeline = build_feature_pipeline()
    feature_model = feature_pipeline.fit(cleaned_df)
    featured_df = feature_model.transform(cleaned_df)

    train_df, test_df = featured_df.randomSplit([0.8, 0.2], seed=42)

    model = train_model(train_df)
    metrics = evaluate_model(model, test_df)

    return {
        "validation": validation,
        "metrics": metrics,
        "model": model,
    }
