"""
Main entry point for the Car Price Prediction ML pipeline.

Usage:
    python -m src.main [--data-path <path>]
"""

import argparse
import sys

from src.pipeline import run_pipeline


def parse_args(args: list = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Car Price Prediction with PySpark Linear Regression",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="",
        help="Path to the input CSV file (default: DATA_PATH env var or data/cars.csv)",
    )
    return parser.parse_args(args)


def main(args: list = None) -> None:
    """Run the ML pipeline and print results."""
    parsed = parse_args(args)

    print("=" * 60)
    print("Car Price Prediction - PySpark Linear Regression")
    print("=" * 60)

    results = run_pipeline(data_path=parsed.data_path)

    validation = results["validation"]
    print("\nData Validation:")
    print(f"  Total rows after cleaning: {validation['total_rows']}")
    if validation["issues"]:
        print(f"  Issues found: {validation['issues']}")
    else:
        print("  No data quality issues found.")

    metrics = results["metrics"]
    print("\nModel Evaluation Metrics:")
    print(f"  RMSE: {metrics['rmse']:.2f}")
    print(f"  R-squared: {metrics['r2']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main() or 0)
