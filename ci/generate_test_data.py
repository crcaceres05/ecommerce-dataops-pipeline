"""
ci/generate_test_data.py
Genera datos sintéticos para el pipeline de CI.
No usa Kaggle API — funciona en cualquier entorno sin credenciales.
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

# Rutas
DB_PATH  = Path("data/processed/warehouse.duckdb")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

random.seed(42)
np.random.seed(42)

N_ORDERS   = 500
N_PRODUCTS = 100
N_CUSTOMERS = 400

conn = duckdb.connect(str(DB_PATH))

print("Generando datos sintéticos para CI...")

# ── raw_customers ──────────────────────────────────────────────────────────────
states = ["SP", "RJ", "MG", "RS", "PR", "BA", "SC", "GO", "PE", "CE"]
customers = pd.DataFrame({
    "customer_id":         [f"cust_{i:04d}" for i in range(N_CUSTOMERS)],
    "customer_unique_id":  [f"uniq_{i:04d}" for i in range(N_CUSTOMERS)],
    "customer_zip_code_prefix": np.random.randint(10000, 99999, N_CUSTOMERS),
    "customer_city":       np.random.choice(["sao paulo", "rio de janeiro", "belo horizonte", "curitiba"], N_CUSTOMERS),
    "customer_state":      np.random.choice(states, N_CUSTOMERS),
})
conn.execute("DROP TABLE IF EXISTS raw_customers")
conn.execute("CREATE TABLE raw_customers AS SELECT * FROM customers")
print(f"  ✓ raw_customers: {len(customers)} filas")

# ── raw_products ───────────────────────────────────────────────────────────────
categories = ["electronics", "furniture", "toys", "sports", "beauty", "books", "clothing", "garden"]
products = pd.DataFrame({
    "product_id":               [f"prod_{i:04d}" for i in range(N_PRODUCTS)],
    "product_category_name":    np.random.choice(categories, N_PRODUCTS),
    "product_name_lenght":      np.random.randint(10, 60, N_PRODUCTS),
    "product_description_lenght": np.random.randint(100, 1000, N_PRODUCTS),
    "product_photos_qty":       np.random.randint(1, 6, N_PRODUCTS),
    "product_weight_g":         np.random.randint(100, 5000, N_PRODUCTS),
    "product_length_cm":        np.random.randint(10, 80, N_PRODUCTS),
    "product_height_cm":        np.random.randint(5, 40, N_PRODUCTS),
    "product_width_cm":         np.random.randint(10, 60, N_PRODUCTS),
})
conn.execute("DROP TABLE IF EXISTS raw_products")
conn.execute("CREATE TABLE raw_products AS SELECT * FROM products")
print(f"  ✓ raw_products: {len(products)} filas")

# ── raw_sellers ────────────────────────────────────────────────────────────────
sellers = pd.DataFrame({
    "seller_id":               [f"sell_{i:03d}" for i in range(50)],
    "seller_zip_code_prefix":  np.random.randint(10000, 99999, 50),
    "seller_city":             np.random.choice(["sao paulo", "curitiba", "rio de janeiro"], 50),
    "seller_state":            np.random.choice(states, 50),
})
conn.execute("DROP TABLE IF EXISTS raw_sellers")
conn.execute("CREATE TABLE raw_sellers AS SELECT * FROM sellers")
print(f"  ✓ raw_sellers: {len(sellers)} filas")

# ── raw_orders ─────────────────────────────────────────────────────────────────
statuses = ["delivered"] * 80 + ["shipped"] * 10 + ["canceled"] * 5 + ["invoiced"] * 3 + ["processing"] * 2
base_date = datetime(2017, 1, 1)

order_rows = []
for i in range(N_ORDERS):
    purchased = base_date + timedelta(days=random.randint(0, 700))
    approved  = purchased + timedelta(hours=random.randint(1, 24))
    shipped   = approved  + timedelta(days=random.randint(1, 5))
    estimated = shipped   + timedelta(days=random.randint(7, 20))
    delivered = shipped   + timedelta(days=random.randint(3, 18))
    status    = random.choice(statuses)

    order_rows.append({
        "order_id":                       f"ord_{i:05d}",
        "customer_id":                    f"cust_{random.randint(0, N_CUSTOMERS-1):04d}",
        "order_status":                   status,
        "order_purchase_timestamp":       purchased.strftime("%Y-%m-%d %H:%M:%S"),
        "order_approved_at":              approved.strftime("%Y-%m-%d %H:%M:%S"),
        "order_delivered_carrier_date":   shipped.strftime("%Y-%m-%d %H:%M:%S"),
        "order_delivered_customer_date":  delivered.strftime("%Y-%m-%d %H:%M:%S") if status == "delivered" else None,
        "order_estimated_delivery_date":  estimated.strftime("%Y-%m-%d %H:%M:%S"),
    })

orders = pd.DataFrame(order_rows)
conn.execute("DROP TABLE IF EXISTS raw_orders")
conn.execute("CREATE TABLE raw_orders AS SELECT * FROM orders")
print(f"  ✓ raw_orders: {len(orders)} filas")

# ── raw_order_items ────────────────────────────────────────────────────────────
items = []
for i in range(N_ORDERS):
    n_items = random.randint(1, 4)
    for j in range(n_items):
        items.append({
            "order_id":           f"ord_{i:05d}",
            "order_item_id":      j + 1,
            "product_id":         f"prod_{random.randint(0, N_PRODUCTS-1):04d}",
            "seller_id":          f"sell_{random.randint(0, 49):03d}",
            "shipping_limit_date": (base_date + timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d %H:%M:%S"),
            "price":              round(random.uniform(10, 500), 2),
            "freight_value":      round(random.uniform(5, 50), 2),
        })

order_items = pd.DataFrame(items)
conn.execute("DROP TABLE IF EXISTS raw_order_items")
conn.execute("CREATE TABLE raw_order_items AS SELECT * FROM order_items")
print(f"  ✓ raw_order_items: {len(order_items)} filas")

# ── raw_order_reviews ──────────────────────────────────────────────────────────
reviews = pd.DataFrame({
    "review_id":                [f"rev_{i:05d}" for i in range(N_ORDERS)],
    "order_id":                 [f"ord_{i:05d}" for i in range(N_ORDERS)],
    "review_score":             np.random.randint(1, 6, N_ORDERS),
    "review_comment_title":     ["ok"] * N_ORDERS,
    "review_comment_message":   ["good product"] * N_ORDERS,
    "review_creation_date":     [(base_date + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(N_ORDERS)],
    "review_answer_timestamp":  [(base_date + timedelta(days=i+1)).strftime("%Y-%m-%d %H:%M:%S") for i in range(N_ORDERS)],
})
conn.execute("DROP TABLE IF EXISTS raw_order_reviews")
conn.execute("CREATE TABLE raw_order_reviews AS SELECT * FROM reviews")
print(f"  ✓ raw_order_reviews: {len(reviews)} filas")

# ── raw_order_payments ─────────────────────────────────────────────────────────
payments = pd.DataFrame({
    "order_id":            [f"ord_{i:05d}" for i in range(N_ORDERS)],
    "payment_sequential":  [1] * N_ORDERS,
    "payment_type":        np.random.choice(["credit_card", "boleto", "voucher", "debit_card"], N_ORDERS),
    "payment_installments": np.random.randint(1, 12, N_ORDERS),
    "payment_value":       np.random.uniform(20, 1000, N_ORDERS).round(2),
})
conn.execute("DROP TABLE IF EXISTS raw_order_payments")
conn.execute("CREATE TABLE raw_order_payments AS SELECT * FROM payments")
print(f"  ✓ raw_order_payments: {len(payments)} filas")

conn.close()
print("\nDatos de CI generados exitosamente ✓")
print(f"DuckDB en: {DB_PATH}")