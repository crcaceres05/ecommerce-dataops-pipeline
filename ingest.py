"""
ingest.py — Fase 1: Descarga y carga de datos raw a DuckDB
Pipeline: Kaggle API → CSV → DuckDB (capa raw)
"""

import os
import logging
import zipfile
import time
from pathlib import Path
from datetime import datetime

import duckdb
import pandas as pd
from dotenv import load_dotenv

# ── Configuración ──────────────────────────────────────────────────────────────

load_dotenv()

RAW_PATH     = Path(os.getenv("RAW_DATA_PATH", "data/raw"))
DB_PATH      = Path(os.getenv("DB_PATH", "data/processed/warehouse.duckdb"))
LOGS_PATH    = Path(os.getenv("LOGS_PATH", "logs"))
DATASET_SLUG = "olistbr/brazilian-ecommerce"

# Tablas que vamos a cargar y sus archivos CSV
TABLES = {
    "raw_orders":          "olist_orders_dataset.csv",
    "raw_order_items":     "olist_order_items_dataset.csv",
    "raw_products":        "olist_products_dataset.csv",
    "raw_customers":       "olist_customers_dataset.csv",
    "raw_order_reviews":   "olist_order_reviews_dataset.csv",
    "raw_order_payments":  "olist_order_payments_dataset.csv",
    "raw_sellers":         "olist_sellers_dataset.csv",
}

# ── Logging ────────────────────────────────────────────────────────────────────

LOGS_PATH.mkdir(parents=True, exist_ok=True)
log_file = LOGS_PATH / f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),        # también muestra en consola
    ],
)
log = logging.getLogger(__name__)

# ── Funciones ──────────────────────────────────────────────────────────────────

def download_dataset() -> None:
    """Descarga el dataset de Kaggle si no existe ya en data/raw/."""
    if any(RAW_PATH.glob("*.csv")):
        log.info("Dataset ya existe en %s — saltando descarga.", RAW_PATH)
        return

    RAW_PATH.mkdir(parents=True, exist_ok=True)
    log.info("Descargando dataset '%s' desde Kaggle...", DATASET_SLUG)

    # La librería kaggle usa ~/.kaggle/kaggle.json automáticamente
    import kaggle
    kaggle.api.dataset_download_files(
        DATASET_SLUG,
        path=str(RAW_PATH),
        unzip=True,
    )
    log.info("Descarga completa. Archivos en %s", RAW_PATH)


def load_csv_to_duckdb(conn: duckdb.DuckDBPyConnection) -> dict:
    """
    Carga cada CSV como tabla en DuckDB.
    Retorna un dict con estadísticas de cada tabla cargada.
    """
    stats = {}

    for table_name, filename in TABLES.items():
        csv_path = RAW_PATH / filename

        if not csv_path.exists():
            log.warning("Archivo no encontrado: %s — saltando.", csv_path)
            continue

        start = time.time()
        log.info("Cargando %s → tabla '%s'...", filename, table_name)

        # Lee el CSV con pandas para poder inspeccionar antes de cargar
        df = pd.read_csv(csv_path, low_memory=False)

        # Registra el DataFrame en DuckDB y crea la tabla
        # Si ya existe la tabla, la reemplaza (idempotente)
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(
            f"CREATE TABLE {table_name} AS SELECT * FROM df"
        )

        elapsed = time.time() - start
        row_count = conn.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        stats[table_name] = {
            "rows":     row_count,
            "columns":  len(df.columns),
            "elapsed_s": round(elapsed, 2),
        }
        log.info(
            "  ✓ %s: %s filas, %s columnas — %.2fs",
            table_name, f"{row_count:,}", len(df.columns), elapsed,
        )

    return stats


def validate_load(conn: duckdb.DuckDBPyConnection, stats: dict) -> bool:
    """
    Validación básica post-carga:
    - Todas las tablas esperadas existen
    - Ninguna tabla está vacía
    Retorna True si todo está bien.
    """
    log.info("── Validando carga ──────────────────────────")
    all_ok = True

    for table_name in TABLES:
        if table_name not in stats:
            log.error("FALLO: tabla '%s' no fue cargada.", table_name)
            all_ok = False
            continue

        if stats[table_name]["rows"] == 0:
            log.error("FALLO: tabla '%s' está vacía.", table_name)
            all_ok = False
        else:
            log.info("  ✓ %s OK (%s filas)", table_name, f"{stats[table_name]['rows']:,}")

    return all_ok


def print_summary(stats: dict) -> None:
    """Imprime resumen del run en consola."""
    log.info("── Resumen del run ──────────────────────────")
    total_rows = sum(s["rows"] for s in stats.values())
    total_time = sum(s["elapsed_s"] for s in stats.values())
    log.info("Tablas cargadas : %s", len(stats))
    log.info("Total filas     : %s", f"{total_rows:,}")
    log.info("Tiempo total    : %.2fs", total_time)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    log.info("══════════════════════════════════════════")
    log.info("  INGEST PIPELINE — inicio")
    log.info("══════════════════════════════════════════")

    # 1. Descarga
    download_dataset()

    # 2. Conecta a DuckDB (crea el archivo si no existe)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.info("Conectando a DuckDB en %s", DB_PATH)
    conn = duckdb.connect(str(DB_PATH))

    # 3. Carga CSVs
    stats = load_csv_to_duckdb(conn)

    # 4. Valida
    ok = validate_load(conn, stats)

    # 5. Resumen
    print_summary(stats)

    conn.close()

    if not ok:
        log.error("Pipeline terminó con errores.")
        raise SystemExit(1)

    log.info("Pipeline completado exitosamente ✓")


if __name__ == "__main__":
    main()