"""
Deploy pipeline artifacts to Databricks workspace.

Uploads data to Unity Catalog Volumes, imports notebooks,
and configures jobs in Databricks.
Requires DATABRICKS_HOST and DATABRICKS_TOKEN environment variables.
"""

import base64
import os
import sys

import requests

REQUEST_TIMEOUT = 30


def get_auth_header() -> dict:
    token = os.environ.get("DATABRICKS_TOKEN", "")
    if not token:
        print("ERROR: DATABRICKS_TOKEN environment variable is required")
        sys.exit(1)
    return {"Authorization": f"Bearer {token}"}


def get_host() -> str:
    host = os.environ.get("DATABRICKS_HOST", "")
    if not host:
        print("ERROR: DATABRICKS_HOST environment variable is required")
        sys.exit(1)
    return host.rstrip("/")


def ensure_uc_resources() -> None:
    """Ensure Unity Catalog schema and volume exist."""
    host = get_host()
    headers = {**get_auth_header(), "Content-Type": "application/json"}

    resp = requests.get(
        f"{host}/api/2.1/unity-catalog/schemas",
        headers=headers,
        params={"catalog_name": "workspace"},
        timeout=REQUEST_TIMEOUT,
    )
    schemas = [s["name"] for s in resp.json().get("schemas", [])]

    if "esteira" not in schemas:
        requests.post(
            f"{host}/api/2.1/unity-catalog/schemas",
            headers=headers,
            json={
                "name": "esteira",
                "catalog_name": "workspace",
                "comment": "ML Pipeline - Car Price Prediction",
            },
            timeout=REQUEST_TIMEOUT,
        )
        print("  Created schema: workspace.esteira")

    resp = requests.get(
        f"{host}/api/2.1/unity-catalog/volumes",
        headers=headers,
        params={"catalog_name": "workspace", "schema_name": "esteira"},
        timeout=REQUEST_TIMEOUT,
    )
    volumes = [v["name"] for v in resp.json().get("volumes", [])]

    if "data" not in volumes:
        requests.post(
            f"{host}/api/2.1/unity-catalog/volumes",
            headers=headers,
            json={
                "name": "data",
                "catalog_name": "workspace",
                "schema_name": "esteira",
                "volume_type": "MANAGED",
                "comment": "Data storage for ML pipeline",
            },
            timeout=REQUEST_TIMEOUT,
        )
        print("  Created volume: workspace.esteira.data")


def upload_file_to_volume(local_path: str, volume_path: str) -> None:
    """Upload a file to a Unity Catalog Volume via the Files API."""
    host = get_host()
    headers = {**get_auth_header(), "Content-Type": "application/octet-stream"}

    with open(local_path, "rb") as f:
        data = f.read()

    resp = requests.put(
        f"{host}/api/2.0/fs/files/{volume_path}",
        headers=headers,
        data=data,
        timeout=REQUEST_TIMEOUT,
    )

    if resp.status_code in (200, 204):
        print(f"  Uploaded: {local_path} -> /{volume_path}")
    else:
        print(f"  ERROR uploading {local_path}: {resp.status_code} - {resp.text}")
        sys.exit(1)


def import_notebook(local_path: str, workspace_path: str) -> None:
    """Import a Python notebook to Databricks workspace."""
    host = get_host()
    headers = {**get_auth_header(), "Content-Type": "application/json"}

    parent_dir = "/".join(workspace_path.rsplit("/", 1)[:-1])
    requests.post(
        f"{host}/api/2.0/workspace/mkdirs",
        headers=headers,
        json={"path": parent_dir},
        timeout=REQUEST_TIMEOUT,
    )

    with open(local_path, "r") as f:
        content = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    payload = {
        "path": workspace_path,
        "language": "PYTHON",
        "overwrite": True,
        "content": content,
        "format": "SOURCE",
    }

    resp = requests.post(
        f"{host}/api/2.0/workspace/import", headers=headers, json=payload, timeout=REQUEST_TIMEOUT
    )
    if resp.status_code == 200:
        print(f"  Imported notebook: {workspace_path}")
    else:
        print(f"  ERROR importing notebook: {resp.status_code} - {resp.text}")
        sys.exit(1)


def create_or_update_job(job_config: dict) -> int:
    """Create or update a Databricks job for the ML pipeline."""
    host = get_host()
    headers = {**get_auth_header(), "Content-Type": "application/json"}

    resp = requests.get(f"{host}/api/2.1/jobs/list", headers=headers, timeout=REQUEST_TIMEOUT)
    existing_jobs = resp.json().get("jobs", [])

    job_name = job_config["name"]
    existing_job = next((j for j in existing_jobs if j["settings"]["name"] == job_name), None)

    if existing_job:
        job_id = existing_job["job_id"]
        payload = {"job_id": job_id, "new_settings": job_config}
        requests.post(
            f"{host}/api/2.1/jobs/reset", headers=headers, json=payload, timeout=REQUEST_TIMEOUT
        )
        print(f"  Updated job '{job_name}' (ID: {job_id})")
    else:
        resp = requests.post(
            f"{host}/api/2.1/jobs/create", headers=headers, json=job_config, timeout=REQUEST_TIMEOUT
        )
        job_id = resp.json().get("job_id", 0)
        print(f"  Created job '{job_name}' (ID: {job_id})")

    return job_id


def main() -> None:
    """Deploy all artifacts to Databricks."""
    print("=" * 60)
    print("Deploying to Databricks")
    print("=" * 60)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("\n[0/4] Ensuring Unity Catalog resources...")
    ensure_uc_resources()

    print("\n[1/4] Uploading data to Unity Catalog Volume...")
    data_file = os.path.join(project_root, "data", "cars.csv")
    upload_file_to_volume(data_file, "Volumes/workspace/esteira/data/cars.csv")

    print("\n[2/4] Importing notebook...")
    notebook_file = os.path.join(project_root, "databricks", "notebook_pipeline.py")
    import_notebook(notebook_file, "/Shared/esteira/car_price_prediction")

    print("\n[3/4] Creating/updating job...")
    cluster_id = os.environ.get("DATABRICKS_CLUSTER_ID", "")

    job_config = {
        "name": "Car Price Prediction - ML Pipeline",
        "tasks": [
            {
                "task_key": "ml_pipeline",
                "description": "Run the car price prediction ML pipeline",
                "notebook_task": {
                    "notebook_path": "/Shared/esteira/car_price_prediction",
                    "source": "WORKSPACE",
                },
            }
        ],
        "tags": {"project": "esteira", "type": "ml-pipeline"},
    }

    use_serverless = os.environ.get("DATABRICKS_SERVERLESS", "true").lower() == "true"

    if cluster_id:
        job_config["tasks"][0]["existing_cluster_id"] = cluster_id
    elif use_serverless:
        job_config["tasks"][0]["environment_key"] = "default"
        job_config["environments"] = [{"environment_key": "default", "spec": {"client": "1"}}]
    else:
        job_config["tasks"][0]["new_cluster"] = {
            "spark_version": "15.4.x-scala2.12",
            "node_type_id": "i3.xlarge",
            "num_workers": 0,
            "spark_conf": {"spark.master": "local[*]"},
        }

    job_id = create_or_update_job(job_config)

    host = get_host()
    print(f"\n{'=' * 60}")
    print("[4/4] Deployment complete!")
    print(f"  Notebook: {host}/#workspace/Shared/esteira/car_price_prediction")
    print(f"  Job ID: {job_id}")
    print("  Data: /Volumes/workspace/esteira/data/cars.csv")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
