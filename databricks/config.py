"""
Databricks workspace configuration.

All sensitive values are read from environment variables.
Never hardcode tokens, hosts, or credentials in this file.
"""

import os


def get_databricks_config() -> dict:
    """
    Retrieve Databricks configuration from environment variables.

    Required env vars:
        DATABRICKS_HOST: Workspace URL (e.g. https://dbc-xxx.cloud.databricks.com)
        DATABRICKS_TOKEN: Personal access token

    Optional env vars:
        DATABRICKS_CLUSTER_ID: Cluster ID for job execution
        UC_DATA_PATH: Path to data in Unity Catalog Volume
        UC_MODEL_PATH: Path to save models in Unity Catalog Volume
    """
    host = os.environ.get("DATABRICKS_HOST", "")
    token = os.environ.get("DATABRICKS_TOKEN", "")

    if not host or not token:
        raise EnvironmentError(
            "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables are required. "
            "Set them before running the pipeline."
        )

    return {
        "host": host.rstrip("/"),
        "token": token,
        "cluster_id": os.environ.get("DATABRICKS_CLUSTER_ID", ""),
        "data_path": os.environ.get("UC_DATA_PATH", "/Volumes/workspace/esteira/data/cars.csv"),
        "model_path": os.environ.get("UC_MODEL_PATH", "/Volumes/workspace/esteira/data/models"),
    }
