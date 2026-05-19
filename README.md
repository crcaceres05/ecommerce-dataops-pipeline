# E-Commerce DataOps Pipeline

![CI](https://github.com/crcaceres05/ecommerce-dataops-pipeline/actions/workflows/ci.yml/badge.svg)
![dbt](https://img.shields.io/badge/dbt-1.8-orange)
![Airflow](https://img.shields.io/badge/Airflow-2.9-blue)
![Python](https://img.shields.io/badge/Python-3.10-green)

Pipeline de DataOps end-to-end sobre el dataset público de e-commerce brasileño (Olist) — 100,000 órdenes reales, 7 tablas, 420,000+ filas totales.

---

## Dashboard

![Dashboard](docs/images/dashboard.png)

| Métrica | Valor |
|---|---|
| % Entregas a tiempo | 93.3% |
| Promedio días de entrega | 12.59 días |
| Revenue peak mensual | ~$1.2M |
| Período del dataset | 2017 – 2018 |

---

## Arquitectura

![Arquitectura](https://mermaid.ink/img/pako:eNpVkE1qwzAQha8itHIKdhInceJFoYsuSqGlm6KFkEZOhPVjJLkhlNy9si1KoRt53rwZpDekrECak6xrBcfBUlitxJGWR69JUXu_OVvuDilMU5rmqZumVZpW05Sm2ZCmWZMWqZMWeZMWeZMWeZMWeZMWadmmZauWLVu2bNmyZcuWLVu2bNmyZcuWLVu2bNmyZcuWLVu2bNmyZcuWLVu2bNmy_QMbkUcS?type=png)
---

## Stack

| Capa | Herramienta | Propósito |
|------|-------------|-----------|
| Ingesta | Python + DuckDB | Descarga Kaggle API → warehouse local |
| Transformación | dbt Core | 3 capas: staging / intermediate / marts |
| Calidad | Great Expectations | Validaciones antes y después de dbt |
| Orquestación | Apache Airflow | DAG diario con reintentos automáticos |
| CI/CD | GitHub Actions | dbt test + pytest en cada PR |
| Visualización | Metabase | Dashboard de negocio |

---

## Estructura del proyecto
---

## Pipeline en Airflow
| Task | Descripción |
|------|-------------|
| `ingest_raw` | Descarga datos de Kaggle y carga 7 tablas a DuckDB |
| `validate_raw` | GE — bloquea si hay datos sucios en raw |
| `run_dbt` | dbt run + dbt test — 6 modelos, 16 tests |
| `validate_marts` | GE — valida output antes del dashboard |

Schedule: diario 6am · Reintentos: 2 · Retry delay: 5 min

---

## Modelos dbt
**16 tests automáticos:** `unique`, `not_null`, `accepted_values` en campos críticos.

---

## CI/CD
---

## Equivalencias en producción

| Local (este proyecto) | Producción empresarial |
|---|---|
| DuckDB | BigQuery / Snowflake / Redshift |
| Airflow local | Cloud Composer / MWAA / Astronomer |
| GitHub Actions | Misma herramienta |
| Great Expectations | Soda / Monte Carlo |
| dbt Core | dbt Cloud |
| Metabase OSS | Looker / Tableau / Power BI |

---

## Cómo correrlo localmente

```bash
git clone https://github.com/crcaceres05/ecommerce-dataops-pipeline
cd ecommerce-dataops-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install dbt-duckdb great-expectations

# Configura Kaggle API
mkdir -p ~/.kaggle && cp kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json

# Corre el pipeline
python ingest.py
cd dbt_project/ecommerce && dbt run --profiles-dir . && dbt test --profiles-dir .
cd ../.. && python validate.py --stage all
```

---

## Autor

**Cesar Cáceres** · QA Automation Engineer → DataOps Engineer

- GitHub: [@crcaceres05](https://github.com/crcaceres05)
- Dataset: [Brazilian E-Commerce — Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
