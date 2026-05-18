"""
tests/test_ingest.py
Tests unitarios para las funciones de ingesta.
Estos corren en CI con pytest.
"""

import pytest
import duckdb
import pandas as pd
from pathlib import Path


DB_PATH = "data/processed/warehouse.duckdb"


def get_conn():
    return duckdb.connect(DB_PATH, read_only=True)


class TestWarehouseTablas:
    """Verifica que todas las tablas raw existen y tienen datos."""

    TABLAS_ESPERADAS = [
        "raw_orders",
        "raw_order_items",
        "raw_products",
        "raw_customers",
        "raw_order_reviews",
        "raw_order_payments",
        "raw_sellers",
    ]

    def test_todas_las_tablas_existen(self):
        conn = get_conn()
        tablas = conn.execute("SHOW TABLES").df()["name"].tolist()
        conn.close()
        for tabla in self.TABLAS_ESPERADAS:
            assert tabla in tablas, f"Tabla '{tabla}' no encontrada en el warehouse"

    def test_raw_orders_no_vacia(self):
        conn = get_conn()
        count = conn.execute("SELECT COUNT(*) FROM raw_orders").fetchone()[0]
        conn.close()
        assert count > 0, "raw_orders está vacía"

    def test_raw_orders_ids_unicos(self):
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) FROM raw_orders").fetchone()[0]
        unicos = conn.execute("SELECT COUNT(DISTINCT order_id) FROM raw_orders").fetchone()[0]
        conn.close()
        assert total == unicos, f"Hay {total - unicos} order_ids duplicados"

    def test_raw_orders_status_validos(self):
        conn = get_conn()
        invalidos = conn.execute("""
            SELECT COUNT(*) FROM raw_orders
            WHERE order_status NOT IN (
                'delivered','shipped','canceled','unavailable',
                'invoiced','processing','created','approved'
            )
        """).fetchone()[0]
        conn.close()
        assert invalidos == 0, f"Hay {invalidos} órdenes con status inválido"

    def test_precios_positivos(self):
        conn = get_conn()
        negativos = conn.execute(
            "SELECT COUNT(*) FROM raw_order_items WHERE price <= 0"
        ).fetchone()[0]
        conn.close()
        assert negativos == 0, f"Hay {negativos} items con precio <= 0"


class TestMarts:
    """Verifica el output final del pipeline dbt."""

    def test_mart_existe(self):
        conn = get_conn()
        tablas = conn.execute("SHOW TABLES").df()["name"].tolist()
        conn.close()
        assert "orders_daily_summary" in tablas, "El mart orders_daily_summary no existe"

    def test_mart_no_vacio(self):
        conn = get_conn()
        count = conn.execute("SELECT COUNT(*) FROM orders_daily_summary").fetchone()[0]
        conn.close()
        assert count > 0, "El mart está vacío"

    def test_fechas_unicas(self):
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) FROM orders_daily_summary").fetchone()[0]
        unicas = conn.execute(
            "SELECT COUNT(DISTINCT order_date) FROM orders_daily_summary"
        ).fetchone()[0]
        conn.close()
        assert total == unicas, "Hay fechas duplicadas en el mart"

    def test_revenue_no_negativo(self):
        conn = get_conn()
        negativos = conn.execute(
            "SELECT COUNT(*) FROM orders_daily_summary WHERE gross_revenue < 0"
        ).fetchone()[0]
        conn.close()
        assert negativos == 0, f"Hay {negativos} días con revenue negativo"