# E-Commerce DataOps Pipeline

![CI](https://github.com/crcaceres05/ecommerce-dataops-pipeline/actions/workflows/ci.yml/badge.svg)
![dbt](https://img.shields.io/badge/dbt-1.8-orange)
![Airflow](https://img.shields.io/badge/Airflow-2.9-blue)
![Python](https://img.shields.io/badge/Python-3.10-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Pipeline de DataOps end-to-end sobre el dataset público de e-commerce brasileño (Olist) — 100,000 órdenes reales, 7 tablas, 420,000+ filas totales.

Construido como proyecto de portfolio para demostrar el **modern data stack** completo: ingesta automática, transformaciones con dbt, calidad de datos, orquestación con Airflow y CI/CD con GitHub Actions.

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
Kaggle API
│
▼
Python + DuckDB (raw)          ← Fase 1: Ingesta
│
▼
Great Expectations             ← Fase 3: Validación raw
│
▼
dbt Core                       ← Fase 2: Transformación
staging → intermediate → marts
│
▼
Great Expectations             ← Fase 3: Validación marts
│
▼
Metabase Dashboard             ← Fase 6: Visualización
Todo orquestado por Apache Airflow (Fase 4)
Todo testeado por GitHub Actions CI/CD (Fase 5)

---

## Stack

| Capa | Herramienta | Propósito |
|------|-------------|-----------|
| Ingesta | Python + DuckDB | Descarga Kaggle API → data warehouse local |
| Transformación | dbt Core | 3 capas: staging / intermediate / marts |
| Calidad | Great Expectations | Validaciones antes y después de dbt |
| Orquestación | Apache Airflow | DAG diario con reintentos automáticos |
| CI/CD | GitHub Actions | dbt test + pytest en cada PR |
| Visualización | Metabase | Dashboard de negocio |

---

## Estructura del proyecto
ecommerce-dataops-pipeline/
├── ingest.py                  # Fase 1: descarga Kaggle → DuckDB
├── validate.py                # Fase 3: validaciones Great Expectations
├── dbt_project/
│   └── ecommerce/
│       ├── models/
│       │   ├── staging/       # stg_orders, stg_products, stg_customers...
│       │   ├── intermediate/  # int_orders_with_items
│       │   └── marts/         # orders_daily_summary
│       └── profiles.yml
├── dags/
│   └── ecommerce_pipeline.py  # DAG Airflow: 4 tasks en secuencia
├── tests/
│   └── test_ingest.py         # 9 tests unitarios pytest
├── ci/
│   └── generate_test_data.py  # datos sintéticos para CI
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions workflow
└── docs/
└── images/
└── dashboard.png

---

## Pipeline en Airflow
ingest_raw → validate_raw → run_dbt → validate_marts

| Task | Descripción |
|------|-------------|
| `ingest_raw` | Descarga datos de Kaggle y carga 7 tablas a DuckDB |
| `validate_raw` | Great Expectations — bloquea si hay datos sucios |
| `run_dbt` | dbt run + dbt test — 6 modelos, 16 tests |
| `validate_marts` | Great Expectations — valida output antes del dashboard |

Schedule: diario a las 6am · Reintentos: 2 · Retry delay: 5 min

---

## Modelos dbt
raw_orders          raw_order_items     raw_products     raw_customers
│                    │                  │                │
▼                    ▼                  ▼                ▼
stg_orders      stg_order_items      stg_products    stg_customers
│              │
└──────┬────────┘
▼
int_orders_with_items
│
▼
orders_daily_summary  ← mart final (tabla física)

**16 tests automáticos:** unique, not_null, accepted_values en campos críticos.

---

## CI/CD

Cada Push o Pull Request a `main` dispara automáticamente:
dbt-ci job:
→ genera datos sintéticos
→ dbt compile (verifica sintaxis SQL)
→ dbt run (ejecuta los 6 modelos)
→ dbt test (corre los 16 tests)
→ sube warehouse como artifact
python-ci job (depende de dbt-ci):
→ descarga warehouse con marts
→ pytest (9 tests unitarios)

---

## Cómo correrlo localmente

**Requisitos:** Python 3.10+, Git, cuenta en Kaggle

```bash
# 1. Clona el repo
git clone https://github.com/crcaceres05/ecommerce-dataops-pipeline
cd ecommerce-dataops-pipeline

# 2. Crea el entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# 3. Instala dependencias
pip install -r requirements.txt
pip install dbt-duckdb apache-airflow==2.9.3 great-expectations

# 4. Configura Kaggle API
mkdir -p ~/.kaggle
cp tu_kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json

# 5. Corre la ingesta
python ingest.py

# 6. Transforma con dbt
cd dbt_project/ecommerce
dbt run --profiles-dir .
dbt test --profiles-dir .

# 7. Valida calidad
cd ../..
python validate.py --stage all

# 8. Levanta Airflow
export AIRFLOW_HOME=$(pwd)/airflow_home
airflow db migrate
airflow webserver --port 8080 &
airflow scheduler &
```

---

## Equivalencias en producción

Este proyecto usa herramientas gratuitas/locales. En producción empresarial:

| Local | Producción |
|-------|-----------|
| DuckDB | BigQuery / Snowflake / Redshift |
| Airflow local | Cloud Composer / MWAA / Astronomer |
| GitHub Actions | Misma herramienta |
| Great Expectations | Soda / Monte Carlo |
| dbt Core | dbt Cloud |
| Metabase OSS | Looker / Tableau / Power BI |

---

## Autor

**Cesar Cáceres** · QA Automation Engineer → DataOps Engineer
- GitHub: [@crcaceres05](https://github.com/crcaceres05)
- Dataset: [Brazilian E-Commerce (Olist)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
