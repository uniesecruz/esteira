"""
Unit tests for the PySpark ML pipeline.

Tests cover data cleaning, validation, feature engineering,
and model training/evaluation stages.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from src.pipeline import (
    build_feature_pipeline,
    clean_data,
    evaluate_model,
    train_model,
    validate_data,
)


@pytest.fixture(scope="session")
def spark():
    """Create a SparkSession for testing."""
    session = (
        SparkSession.builder.appName("TestCarPricePrediction")
        .master("local[2]")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture
def raw_schema():
    """Schema matching the raw CSV input."""
    return StructType(
        [
            StructField("car_name", StringType(), True),
            StructField("year", IntegerType(), True),
            StructField("selling_price", IntegerType(), True),
            StructField("km_driven", IntegerType(), True),
            StructField("fuel", StringType(), True),
            StructField("seller_type", StringType(), True),
            StructField("transmission", StringType(), True),
            StructField("owner", StringType(), True),
            StructField("mileage", StringType(), True),
            StructField("engine", StringType(), True),
            StructField("max_power", StringType(), True),
            StructField("seats", IntegerType(), True),
        ]
    )


@pytest.fixture
def sample_data(spark, raw_schema):
    """Create a sample DataFrame matching raw CSV structure."""
    data = [
        (
            "Maruti Swift",
            2014,
            450000,
            145500,
            "Diesel",
            "Individual",
            "Manual",
            "First Owner",
            "23.4 kmpl",
            "1248 CC",
            "74 bhp",
            5,
        ),
        (
            "Skoda Rapid",
            2014,
            370000,
            120000,
            "Diesel",
            "Individual",
            "Manual",
            "Second Owner",
            "21.14 kmpl",
            "1498 CC",
            "103.52 bhp",
            5,
        ),
        (
            "Honda City",
            2006,
            158000,
            140000,
            "Petrol",
            "Individual",
            "Manual",
            "Third Owner",
            "17.7 kmpl",
            "1497 CC",
            "78 bhp",
            5,
        ),
        (
            "Hyundai i20",
            2010,
            225000,
            127000,
            "Diesel",
            "Individual",
            "Manual",
            "First Owner",
            "23.0 kmpl",
            "1396 CC",
            "90 bhp",
            5,
        ),
        (
            "Maruti Swift VXI",
            2007,
            130000,
            120000,
            "Petrol",
            "Individual",
            "Manual",
            "First Owner",
            "16.1 kmpl",
            "1298 CC",
            "88.2 bhp",
            5,
        ),
        (
            "Toyota Innova",
            2013,
            720000,
            90000,
            "Diesel",
            "Individual",
            "Manual",
            "First Owner",
            "11.36 kmpl",
            "2494 CC",
            "102 bhp",
            7,
        ),
        (
            "Hyundai Creta",
            2017,
            850000,
            50000,
            "Diesel",
            "Individual",
            "Manual",
            "First Owner",
            "19.67 kmpl",
            "1582 CC",
            "126.2 bhp",
            5,
        ),
        (
            "Ford EcoSport",
            2017,
            580000,
            55000,
            "Diesel",
            "Individual",
            "Manual",
            "First Owner",
            "22.77 kmpl",
            "1498 CC",
            "99 bhp",
            5,
        ),
        (
            "Tata Nexon",
            2018,
            700000,
            38000,
            "Petrol",
            "Individual",
            "Manual",
            "First Owner",
            "17.0 kmpl",
            "1198 CC",
            "108.5 bhp",
            5,
        ),
        (
            "Maruti Baleno",
            2019,
            575000,
            25000,
            "Petrol",
            "Individual",
            "Manual",
            "First Owner",
            "21.01 kmpl",
            "1197 CC",
            "83.1 bhp",
            5,
        ),
    ]
    return spark.createDataFrame(data, schema=raw_schema)


@pytest.fixture
def data_with_nulls(spark, raw_schema):
    """Create a DataFrame with null values for validation tests."""
    data = [
        (
            "Maruti Swift",
            2014,
            450000,
            145500,
            "Diesel",
            "Individual",
            "Manual",
            "First Owner",
            "23.4 kmpl",
            "1248 CC",
            "74 bhp",
            5,
        ),
        (
            "Null Car",
            None,
            None,
            None,
            "Petrol",
            "Individual",
            "Manual",
            "First Owner",
            None,
            None,
            None,
            5,
        ),
        (
            "Another Car",
            2018,
            500000,
            30000,
            "Petrol",
            "Individual",
            "Manual",
            "First Owner",
            "20.0 kmpl",
            "1200 CC",
            "85 bhp",
            5,
        ),
    ]
    return spark.createDataFrame(data, schema=raw_schema)


class TestCleanData:
    """Tests for the clean_data function."""

    def test_mileage_extraction(self, sample_data):
        """Numeric mileage is extracted from string."""
        result = clean_data(sample_data)
        mileage_values = [row.mileage for row in result.select("mileage").collect()]
        assert all(isinstance(v, float) for v in mileage_values)
        assert 23.4 in mileage_values

    def test_engine_extraction(self, sample_data):
        """Numeric engine displacement is extracted from string."""
        result = clean_data(sample_data)
        engine_values = [row.engine for row in result.select("engine").collect()]
        assert all(isinstance(v, float) for v in engine_values)
        assert 1248.0 in engine_values

    def test_max_power_extraction(self, sample_data):
        """Numeric max power is extracted from string."""
        result = clean_data(sample_data)
        power_values = [row.max_power for row in result.select("max_power").collect()]
        assert all(isinstance(v, float) for v in power_values)
        assert 74.0 in power_values

    def test_null_rows_dropped(self, data_with_nulls):
        """Rows with nulls in critical columns are dropped."""
        result = clean_data(data_with_nulls)
        assert result.count() == 2

    def test_column_types_after_cleaning(self, sample_data):
        """Columns have correct types after cleaning."""
        result = clean_data(sample_data)
        schema = {f.name: f.dataType for f in result.schema.fields}
        assert isinstance(schema["year"], IntegerType)
        assert isinstance(schema["selling_price"], IntegerType)
        assert isinstance(schema["mileage"], DoubleType)
        assert isinstance(schema["engine"], DoubleType)
        assert isinstance(schema["max_power"], DoubleType)

    def test_no_data_loss_on_clean_input(self, sample_data):
        """No rows are lost when input has no nulls."""
        result = clean_data(sample_data)
        assert result.count() == sample_data.count()


class TestValidateData:
    """Tests for the validate_data function."""

    def test_valid_data_no_issues(self, sample_data):
        """Clean data produces no validation issues."""
        cleaned = clean_data(sample_data)
        result = validate_data(cleaned)
        assert result["total_rows"] == 10
        assert result["issues"] == []

    def test_empty_dataframe(self, spark, raw_schema):
        """Empty DataFrame is flagged as an issue."""
        empty_df = spark.createDataFrame([], schema=raw_schema)
        result = validate_data(empty_df)
        assert result["total_rows"] == 0
        assert "DataFrame is empty" in result["issues"]

    def test_missing_columns_detected(self, spark):
        """Missing required columns are detected."""
        schema = StructType(
            [
                StructField("year", IntegerType(), True),
                StructField("selling_price", IntegerType(), True),
            ]
        )
        df = spark.createDataFrame([(2020, 500000)], schema=schema)
        result = validate_data(df)
        assert any("Missing columns" in issue for issue in result["issues"])

    def test_null_values_reported(self, spark, raw_schema):
        """Null values in critical columns are reported."""
        data = [
            (
                "Car",
                2014,
                450000,
                145500,
                "Diesel",
                "Individual",
                "Manual",
                "First Owner",
                "23.4 kmpl",
                "1248 CC",
                "74 bhp",
                None,
            ),
        ]
        df = spark.createDataFrame(data, schema=raw_schema)
        cleaned = clean_data(df)
        result = validate_data(cleaned)
        assert any("null" in issue for issue in result["issues"])


class TestFeaturePipeline:
    """Tests for the feature engineering pipeline."""

    def test_pipeline_produces_features_column(self, sample_data):
        """Feature pipeline adds a 'features' column."""
        cleaned = clean_data(sample_data)
        pipeline = build_feature_pipeline()
        model = pipeline.fit(cleaned)
        transformed = model.transform(cleaned)
        assert "features" in transformed.columns

    def test_indexed_columns_created(self, sample_data):
        """StringIndexer creates indexed columns for categoricals."""
        cleaned = clean_data(sample_data)
        pipeline = build_feature_pipeline()
        model = pipeline.fit(cleaned)
        transformed = model.transform(cleaned)
        expected = [
            "fuel_index",
            "seller_type_index",
            "transmission_index",
            "owner_index",
        ]
        for col in expected:
            assert col in transformed.columns

    def test_feature_vector_size(self, sample_data):
        """Feature vector has the expected number of elements."""
        cleaned = clean_data(sample_data)
        pipeline = build_feature_pipeline()
        model = pipeline.fit(cleaned)
        transformed = model.transform(cleaned)
        first_row = transformed.select("features").first()
        # 6 numeric + 4 indexed categorical = 10 features
        assert len(first_row.features) == 10


class TestModelTrainingAndEvaluation:
    """Tests for model training and evaluation."""

    def test_model_trains_successfully(self, sample_data):
        """Model training completes without errors."""
        cleaned = clean_data(sample_data)
        pipeline = build_feature_pipeline()
        featured = pipeline.fit(cleaned).transform(cleaned)
        model = train_model(featured, max_iter=10)
        assert model is not None
        assert hasattr(model, "coefficients")

    def test_model_produces_predictions(self, sample_data):
        """Trained model produces prediction column."""
        cleaned = clean_data(sample_data)
        pipeline = build_feature_pipeline()
        featured = pipeline.fit(cleaned).transform(cleaned)
        model = train_model(featured, max_iter=10)
        predictions = model.transform(featured)
        assert "prediction" in predictions.columns
        assert predictions.filter(predictions.prediction.isNotNull()).count() > 0

    def test_evaluate_returns_metrics(self, sample_data):
        """Evaluation returns both RMSE and R-squared metrics."""
        cleaned = clean_data(sample_data)
        pipeline = build_feature_pipeline()
        featured = pipeline.fit(cleaned).transform(cleaned)
        model = train_model(featured, max_iter=10)
        metrics = evaluate_model(model, featured)
        assert "rmse" in metrics
        assert "r2" in metrics
        assert isinstance(metrics["rmse"], float)
        assert isinstance(metrics["r2"], float)

    def test_rmse_is_non_negative(self, sample_data):
        """RMSE should always be non-negative."""
        cleaned = clean_data(sample_data)
        pipeline = build_feature_pipeline()
        featured = pipeline.fit(cleaned).transform(cleaned)
        model = train_model(featured, max_iter=10)
        metrics = evaluate_model(model, featured)
        assert metrics["rmse"] >= 0
