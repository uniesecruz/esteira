"""
Trigger and monitor a Databricks job run.

Requires DATABRICKS_HOST and DATABRICKS_TOKEN environment variables.
"""

import os
import sys
import time

import requests

REQUEST_TIMEOUT = 30


def get_headers() -> dict:
    token = os.environ.get("DATABRICKS_TOKEN", "")
    if not token:
        print("ERROR: DATABRICKS_TOKEN environment variable is required")
        sys.exit(1)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def get_host() -> str:
    host = os.environ.get("DATABRICKS_HOST", "")
    if not host:
        print("ERROR: DATABRICKS_HOST environment variable is required")
        sys.exit(1)
    return host.rstrip("/")


def find_job_id(job_name: str = "Car Price Prediction - ML Pipeline") -> int:
    """Find the job ID by name."""
    host = get_host()
    headers = get_headers()

    resp = requests.get(f"{host}/api/2.1/jobs/list", headers=headers, timeout=REQUEST_TIMEOUT)
    jobs = resp.json().get("jobs", [])

    for job in jobs:
        if job["settings"]["name"] == job_name:
            return job["job_id"]

    print(f"ERROR: Job '{job_name}' not found. Run deploy_to_databricks.py first.")
    sys.exit(1)


def run_job(job_id: int) -> int:
    """Trigger a job run and return the run ID."""
    host = get_host()
    headers = get_headers()

    resp = requests.post(
        f"{host}/api/2.1/jobs/run-now",
        headers=headers,
        json={"job_id": job_id},
        timeout=REQUEST_TIMEOUT,
    )

    if resp.status_code != 200:
        print(f"ERROR: Failed to trigger job: {resp.status_code} - {resp.text}")
        sys.exit(1)

    run_id = resp.json()["run_id"]
    print(f"Job triggered. Run ID: {run_id}")
    return run_id


def wait_for_completion(run_id: int, poll_interval: int = 15) -> dict:
    """Poll until the job run completes."""
    host = get_host()
    headers = get_headers()

    terminal_states = {"TERMINATED", "SKIPPED", "INTERNAL_ERROR"}

    while True:
        resp = requests.get(
            f"{host}/api/2.1/jobs/runs/get",
            headers=headers,
            params={"run_id": run_id},
            timeout=REQUEST_TIMEOUT,
        )
        run_data = resp.json()
        state = run_data.get("state", {})
        life_cycle = state.get("life_cycle_state", "UNKNOWN")
        result = state.get("result_state", "")

        print(f"  Status: {life_cycle} {f'({result})' if result else ''}")

        if life_cycle in terminal_states:
            return run_data

        time.sleep(poll_interval)


def main() -> None:
    """Run the Databricks ML pipeline job."""
    print("=" * 60)
    print("Running Databricks ML Pipeline Job")
    print("=" * 60)

    job_id = find_job_id()
    print(f"Found job ID: {job_id}")

    run_id = run_job(job_id)

    print("\nWaiting for completion...")
    result = wait_for_completion(run_id)

    state = result.get("state", {})
    result_state = state.get("result_state", "UNKNOWN")
    host = get_host()

    print(f"\n{'=' * 60}")
    print(f"Result: {result_state}")
    print(f"Run URL: {host}/#job/{job_id}/run/{run_id}")
    print(f"{'=' * 60}")

    if result_state != "SUCCESS":
        message = state.get("state_message", "No details available")
        print(f"Error: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
