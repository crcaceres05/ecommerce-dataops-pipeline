"""
dags/ecommerce_pipeline.py
DAG principal del pipeline de e-commerce.

Flujo:
  ingest_raw → validate_raw → run_dbt → validate_marts

Schedule: diario a las 6am (o manual)
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# ── Configuración ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DBT_PROJECT  = PROJECT_ROOT / "dbt_project" / "ecommerce"
DBT_BIN     = PROJECT_ROOT / ".venv" / "bin" / "dbt"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python3"

DEFAULT_ARGS = {
    "owner":            "cesar",
    "depends_on_past":  False,
    "start_date":       days_ago(1),
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
}

# ── Tasks ──────────────────────────────────────────────────────────────────────

def task_ingest_raw(**context):
    import logging
    log = logging.getLogger(__name__)

    script = PROJECT_ROOT / "ingest.py"
    log.info("Corriendo ingest.py desde %s", PROJECT_ROOT)

    result = subprocess.run(
        [str(VENV_PYTHON), str(script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        log.info(result.stdout)
    if result.stderr:
        log.warning(result.stderr)

    if result.returncode != 0:
        raise Exception(f"ingest.py falló con código {result.returncode}")

    log.info("Ingesta completada ✓")


def task_validate_raw(**context):
    import logging
    log = logging.getLogger(__name__)

    script = PROJECT_ROOT / "validate.py"
    log.info("Corriendo validaciones raw...")

    result = subprocess.run(
        [str(VENV_PYTHON), str(script), "--stage", "raw"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        log.info(result.stdout)
    if result.stderr:
        log.warning(result.stderr)

    if result.returncode != 0:
        raise Exception(
            "Validación RAW falló — datos sucios detectados."
        )

    log.info("Validación raw pasó ✓")


def task_run_dbt(**context):
    import logging
    log = logging.getLogger(__name__)

    dbt_bin =DBT_BIN 

    log.info("Corriendo dbt run...")
    result_run = subprocess.run(
        [str(dbt_bin), "run", "--profiles-dir", "."],
        cwd=str(DBT_PROJECT),
        capture_output=True,
        text=True,
    )

    if result_run.stdout:
        log.info(result_run.stdout)
    if result_run.stderr:
        log.warning(result_run.stderr)

    if result_run.returncode != 0:
        raise Exception("dbt run falló")

    log.info("Corriendo dbt test...")
    result_test = subprocess.run(
        [str(dbt_bin), "test", "--profiles-dir", "."],
        cwd=str(DBT_PROJECT),
        capture_output=True,
        text=True,
    )

    if result_test.stdout:
        log.info(result_test.stdout)

    if result_test.returncode != 0:
        raise Exception("dbt test falló")

    log.info("dbt run + test completados ✓")


def task_validate_marts(**context):
    import logging
    log = logging.getLogger(__name__)

    script = PROJECT_ROOT / "validate.py"
    log.info("Corriendo validaciones marts...")

    result = subprocess.run(
        [str(VENV_PYTHON), str(script), "--stage", "marts"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if result.stdout:
        log.info(result.stdout)
    if result.stderr:
        log.warning(result.stderr)

    if result.returncode != 0:
        raise Exception(
            "Validación MARTS falló — output de dbt tiene problemas."
        )

    log.info("Validación marts pasó ✓")


# ── DAG ────────────────────────────────────────────────────────────────────────

with DAG(
    dag_id="ecommerce_pipeline",
    description="Pipeline completo: ingesta → calidad → transformación → validación",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 6 * * *",
    catchup=False,
    tags=["ecommerce", "dataops", "portfolio"],
    doc_md="""
    ## E-Commerce DataOps Pipeline

    Pipeline completo que orquesta:
    1. **ingest_raw** — descarga datos de Kaggle y carga a DuckDB
    2. **validate_raw** — valida calidad de datos crudos (Great Expectations)
    3. **run_dbt** — transforma datos: staging → intermediate → marts
    4. **validate_marts** — valida output final antes del dashboard
    """,
) as dag:

    ingest_raw = PythonOperator(
        task_id="ingest_raw",
        python_callable=task_ingest_raw,
    )

    validate_raw = PythonOperator(
        task_id="validate_raw",
        python_callable=task_validate_raw,
    )

    run_dbt = PythonOperator(
        task_id="run_dbt",
        python_callable=task_run_dbt,
    )

    validate_marts = PythonOperator(
        task_id="validate_marts",
        python_callable=task_validate_marts,
    )

    ingest_raw >> validate_raw >> run_dbt >> validate_marts