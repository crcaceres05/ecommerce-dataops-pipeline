"""
validate.py — Validaciones de calidad con Great Expectations 1.x
API moderna: sin CLI, sin YAML, todo en Python.

Uso:
  python validate.py --stage raw
  python validate.py --stage marts
  python validate.py --stage all
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import great_expectations as gx
import duckdb
import pandas as pd

# ── Logging ────────────────────────────────────────────────────────────────────
LOGS_PATH = Path("logs")
LOGS_PATH.mkdir(exist_ok=True)
log_file = LOGS_PATH / f"validate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

DB_PATH = "data/processed/warehouse.duckdb"


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_table(table_name: str) -> pd.DataFrame:
    """Lee una tabla de DuckDB y la retorna como DataFrame."""
    conn = duckdb.connect(DB_PATH, read_only=True)
    df = conn.execute(f"SELECT * FROM {table_name}").df()
    conn.close()
    return df


def print_result(suite_name: str, results: list) -> bool:
    """Imprime el resumen de resultados y retorna True si todos pasaron."""
    passed = sum(1 for r in results if r["success"])
    total  = len(results)
    all_ok = passed == total

    log.info(
        "  %s — %s/%s expectativas pasaron %s",
        suite_name, passed, total,
        "✓" if all_ok else "✗",
    )

    for r in results:
        if not r["success"]:
            exp  = r["expectation_type"]
            col  = r.get("column", "tabla")
            obs  = r.get("observed_value", "?")
            log.error("    ✗ FALLÓ [%s] columna='%s' valor_observado=%s", exp, col, obs)

    return all_ok


# ── Suites de validación ───────────────────────────────────────────────────────

def validate_raw_orders(context) -> bool:
    log.info("Validando raw_orders...")
    df = load_table("raw_orders")

    suite = context.suites.add(gx.ExpectationSuite(name="raw_orders_suite"))

    batch_def = (
        context.data_sources
        .add_pandas("raw_orders_source")
        .add_dataframe_asset("raw_orders_asset")
        .add_batch_definition_whole_dataframe("raw_orders_batch")
    )

    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="order_id"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="order_status"),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="order_status",
            value_set=[
                "delivered", "shipped", "canceled", "unavailable",
                "invoiced", "processing", "created", "approved",
            ],
        ),
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=90_000, max_value=120_000
        ),
    ]

    results = []
    for exp in expectations:
        r = batch.validate(exp)
        results.append({
            "success":          r.success,
            "expectation_type": type(exp).__name__,
            "column":           getattr(exp, "column", "table"),
            "observed_value":   r.result.get("observed_value"),
        })

    return print_result("raw_orders", results)


def validate_raw_order_items(context) -> bool:
    log.info("Validando raw_order_items...")
    df = load_table("raw_order_items")

    suite = context.suites.add(gx.ExpectationSuite(name="raw_order_items_suite"))

    batch_def = (
        context.data_sources
        .add_pandas("raw_order_items_source")
        .add_dataframe_asset("raw_order_items_asset")
        .add_batch_definition_whole_dataframe("raw_order_items_batch")
    )

    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="product_id"),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="price", min_value=0.01, max_value=10_000
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="freight_value", min_value=0, max_value=500
        ),
        gx.expectations.ExpectColumnMinToBeBetween(
            column="price", min_value=0.01
        ),
    ]

    results = []
    for exp in expectations:
        r = batch.validate(exp)
        results.append({
            "success":          r.success,
            "expectation_type": type(exp).__name__,
            "column":           getattr(exp, "column", "table"),
            "observed_value":   r.result.get("observed_value"),
        })

    return print_result("raw_order_items", results)


def validate_marts(context) -> bool:
    log.info("Validando orders_daily_summary...")
    df = load_table("orders_daily_summary")

    suite = context.suites.add(gx.ExpectationSuite(name="orders_daily_summary_suite"))

    batch_def = (
        context.data_sources
        .add_pandas("marts_source")
        .add_dataframe_asset("marts_asset")
        .add_batch_definition_whole_dataframe("marts_batch")
    )

    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="order_date"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="order_date"),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="gross_revenue", min_value=0
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="on_time_pct", min_value=0, max_value=100,
            mostly=0.95,
        ),
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=600, max_value=800
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="avg_delivery_days", min_value=1, max_value=60,
            mostly=0.90,
        ),
    ]

    results = []
    for exp in expectations:
        r = batch.validate(exp)
        results.append({
            "success":          r.success,
            "expectation_type": type(exp).__name__,
            "column":           getattr(exp, "column", "table"),
            "observed_value":   r.result.get("observed_value"),
        })

    return print_result("orders_daily_summary", results)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=["raw", "marts", "all"],
        default="all",
    )
    args = parser.parse_args()

    log.info("══════════════════════════════════════════")
    log.info("  VALIDACIÓN GE — stage: %s", args.stage)
    log.info("══════════════════════════════════════════")

    # En GE 1.x el contexto efímero no necesita archivos en disco
    context = gx.get_context(mode="ephemeral")

    results = {}

    if args.stage in ("raw", "all"):
        results["raw_orders"]      = validate_raw_orders(context)
        results["raw_order_items"] = validate_raw_order_items(context)

    if args.stage in ("marts", "all"):
        results["marts"] = validate_marts(context)

    # Resumen
    log.info("── Resumen final ─────────────────────────")
    all_passed = True
    for name, ok in results.items():
        log.info("  %-25s %s", name, "✓ PASS" if ok else "✗ FAIL")
        if not ok:
            all_passed = False

    if not all_passed:
        log.error("Una o más validaciones fallaron.")
        sys.exit(1)

    log.info("Todas las validaciones pasaron ✓")


if __name__ == "__main__":
    main()