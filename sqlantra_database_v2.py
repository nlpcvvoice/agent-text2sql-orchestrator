#!/usr/bin/env python3
"""Sqlantra SQLite Database V2 - With Pipeline Layers and Text-to-SQL."""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = "/tmp/sqlantra_v2_demo.db"


def get_db_path():
    return DB_PATH


def reset_database():
    """Reset database to clean state."""
    import os

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_database()
    return True


def init_database():
    """Initialize the database with e-commerce sample data and pipeline layers."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        -- Core Business Tables (E-commerce) --
        
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            channel TEXT NOT NULL,
            customer_id TEXT,
            order_date TEXT,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            raw_data TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            created_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            product_id TEXT,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        );
        
        -- Pipeline Layer Tables (E-commerce Orders) --
        
        CREATE TABLE IF NOT EXISTS bronze_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            raw_data TEXT,
            _source TEXT,
            _ingested_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS silver_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            channel TEXT,
            customer_id TEXT,
            total_amount REAL,
            status TEXT,
            order_date TEXT,
            _curated_at TEXT,
            _domain TEXT
        );
        
        CREATE TABLE IF NOT EXISTS gold_daily_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            channel TEXT,
            total_orders INTEGER,
            total_revenue REAL,
            avg_order_value REAL,
            _processed_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS gold_product_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT,
            product_name TEXT,
            category TEXT,
            total_sold INTEGER,
            total_revenue REAL,
            stock_alert TEXT,
            _processed_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS gold_customer_360 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            total_orders INTEGER,
            total_spent REAL,
            avg_order_value REAL,
            customer_segment TEXT,
            clv_prediction REAL,
            _processed_at TEXT
        );
        
        -- HITL Approvals Table --
        
        CREATE TABLE IF NOT EXISTS hitl_approvals (
            approval_id TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            details TEXT NOT NULL,
            requester TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            comment TEXT,
            notification TEXT,
            created_at TEXT,
            responded_at TEXT
        );
        
        -- Context Memory Log --
        
        CREATE TABLE IF NOT EXISTS context_memory_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_key TEXT,
            memory_value TEXT,
            operation TEXT,
            metadata TEXT,
            created_at TEXT
        );
    """)

    now = datetime.now().isoformat()
    
    # Sample products
    products_data = [
        ("PROD-001", "MacBook Pro 16\"", "Electronics", 2399.00, 50, now),
        ("PROD-002", "iPhone 15 Pro", "Electronics", 999.00, 100, now),
        ("PROD-003", "Sony WH-1000XM5", "Audio", 399.00, 75, now),
        ("PROD-004", "Nike Air Max", "Footwear", 129.00, 200, now),
        ("PROD-005", "Lego Star Wars Set", "Toys", 89.99, 150, now),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?, ?)",
        products_data,
    )
    
    # Sample orders from different channels
    orders_data = [
        ("ORD-001", "Web", "CUST-001", "2026-04-20", 2478.00, "completed", 
         '{"items": [{"product": "MacBook Pro", "qty": 1}], "payment": "credit_card"}', now, now),
        ("ORD-002", "App", "CUST-002", "2026-04-21", 1098.00, "completed",
         '{"items": [{"product": "iPhone 15 Pro", "qty": 1}], "payment": "apple_pay"}', now, now),
        ("ORD-003", "POS", "CUST-003", "2026-04-21", 258.00, "completed",
         '{"items": [{"product": "Nike Air Max", "qty": 2}], "payment": "cash"}', now, now),
        ("ORD-004", "Web", "CUST-001", "2026-04-22", 399.00, "completed",
         '{"items": [{"product": "Sony WH-1000XM5", "qty": 1}], "payment": "credit_card"}', now, now),
        ("ORD-005", "App", "CUST-004", "2026-04-23", 89.99, "pending",
         '{"items": [{"product": "Lego Star Wars", "qty": 1}], "payment": "google_pay"}', now, now),
        ("ORD-006", "API", "CUST-005", "2026-04-24", 4797.00, "completed",
         '{"items": [{"product": "MacBook Pro", "qty": 2}], "payment": "bank_transfer"}', now, now),
        ("ORD-007", "Web", "CUST-002", "2026-04-25", 129.00, "completed",
         '{"items": [{"product": "Nike Air Max", "qty": 1}], "payment": "credit_card"}', now, now),
        ("ORD-008", "App", "CUST-006", "2026-04-26", 1998.00, "completed",
         '{"items": [{"product": "iPhone 15 Pro", "qty": 2}], "payment": "apple_pay"}', now, now),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        orders_data,
    )
    
    # Sample order items
    order_items_data = [
        ("ORD-001", "PROD-001", 1, 2399.00),
        ("ORD-002", "PROD-002", 1, 999.00),
        ("ORD-003", "PROD-004", 2, 129.00),
        ("ORD-004", "PROD-003", 1, 399.00),
        ("ORD-005", "PROD-005", 1, 89.99),
        ("ORD-006", "PROD-001", 2, 2399.00),
        ("ORD-007", "PROD-004", 1, 129.00),
        ("ORD-008", "PROD-002", 2, 999.00),
    ]
    cursor.executemany(
        "INSERT OR REPLACE INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
        order_items_data,
    )

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at: {DB_PATH}")


def get_all_tables():
    """Get all table names."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_table_data(table_name: str, limit: int = 100):
    """Get all data from a table."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = [dict(row) for row in rows]
    except sqlite3.Error as e:
        data = []
        columns = ["error"]
    finally:
        conn.close()

    return {"columns": columns, "data": data}


def query_sql(sql: str, params: tuple = ()):
    """Execute a raw SQL query."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params)
        if sql.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            data = [dict(row) for row in rows]
        else:
            conn.commit()
            data = [{"affected_rows": cursor.rowcount}]
        error = None
    except sqlite3.Error as e:
        data = []
        columns = []
        error = str(e)
    finally:
        conn.close()

    return {"columns": columns, "data": data, "error": error}


def insert_bronze_record(order_id: str, raw_data: dict):
    """Insert order data into bronze layer."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO bronze_orders (order_id, raw_data, _source, _ingested_at) VALUES (?, ?, ?, ?)",
            (order_id, json.dumps(raw_data), "channel_input", datetime.now().isoformat()),
        )
        conn.commit()
        result = {"status": "success", "table": "bronze_orders"}
    except sqlite3.Error as e:
        result = {"status": "error", "error": str(e)}
    finally:
        conn.close()

    return result


def insert_silver_record(order_data: dict):
    """Insert cleaned order data into silver layer."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO silver_orders 
               (order_id, channel, customer_id, total_amount, status, order_date, _curated_at, _domain) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                order_data.get("order_id"),
                order_data.get("channel"),
                order_data.get("customer_id"),
                order_data.get("total_amount"),
                order_data.get("status"),
                order_data.get("order_date"),
                datetime.now().isoformat(),
                "orders",
            ),
        )
        conn.commit()
        result = {"status": "success", "table": "silver_orders"}
    except sqlite3.Error as e:
        result = {"status": "error", "error": str(e)}
    finally:
        conn.close()

    return result


def process_gold_metrics():
    """Process silver data into gold layer metrics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Process daily sales metrics
        cursor.execute("""
            INSERT OR REPLACE INTO gold_daily_sales 
            (date, channel, total_orders, total_revenue, avg_order_value, _processed_at)
            SELECT 
                DATE(order_date) as date,
                channel,
                COUNT(*) as total_orders,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order_value,
                ? as _processed_at
            FROM silver_orders 
            WHERE status = 'completed'
            GROUP BY DATE(order_date), channel
        """, (datetime.now().isoformat(),))
        
        # Process product performance
        cursor.execute("""
            INSERT OR REPLACE INTO gold_product_performance
            (product_id, product_name, category, total_sold, total_revenue, stock_alert, _processed_at)
            SELECT 
                p.product_id,
                p.name,
                p.category,
                SUM(oi.quantity) as total_sold,
                SUM(oi.quantity * oi.unit_price) as total_revenue,
                CASE WHEN p.stock < 20 THEN 'LOW_STOCK' ELSE 'OK' END as stock_alert,
                ? as _processed_at
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.status = 'completed'
            GROUP BY p.product_id, p.name, p.category, p.stock
        """, (datetime.now().isoformat(),))
        
        # Process customer 360
        cursor.execute("""
            INSERT OR REPLACE INTO gold_customer_360
            (customer_id, total_orders, total_spent, avg_order_value, customer_segment, clv_prediction, _processed_at)
            SELECT 
                customer_id,
                COUNT(*) as total_orders,
                SUM(total_amount) as total_spent,
                AVG(total_amount) as avg_order_value,
                CASE 
                    WHEN SUM(total_amount) > 5000 THEN 'VIP'
                    WHEN SUM(total_amount) > 2000 THEN 'PREMIUM'
                    ELSE 'STANDARD'
                END as customer_segment,
                SUM(total_amount) * 1.2 as clv_prediction,
                ? as _processed_at
            FROM silver_orders
            WHERE status = 'completed'
            GROUP BY customer_id
        """, (datetime.now().isoformat(),))
        
        conn.commit()
        result = {"status": "success", "message": "Gold layer metrics processed"}
    except sqlite3.Error as e:
        result = {"status": "error", "error": str(e)}
    finally:
        conn.close()

    return result


def create_approval(
    action_type: str, details: dict, requester: str, notification: str = ""
):
    """Create a HITL approval request."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Use microseconds to ensure uniqueness
    approval_id = f"APR-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    created_at = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO hitl_approvals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            approval_id,
            action_type,
            json.dumps(details),
            requester,
            "pending",
            None,
            notification,
            created_at,
            None,
        ),
    )
    conn.commit()
    conn.close()

    return {"approval_id": approval_id, "status": "pending", "created_at": created_at}


def respond_approval(approval_id: str, approved: bool, comment: str):
    """Respond to an approval request."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    status = "approved" if approved else "rejected"
    responded_at = datetime.now().isoformat()

    cursor.execute(
        "UPDATE hitl_approvals SET status = ?, comment = ?, responded_at = ? WHERE approval_id = ?",
        (status, comment, responded_at, approval_id),
    )
    conn.commit()
    conn.close()

    return {"approval_id": approval_id, "status": status}


def get_pending_approvals():
    """Get all pending approvals."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM hitl_approvals WHERE status = 'pending' ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_all_approvals():
    """Get all approvals."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM hitl_approvals ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def log_context_memory(
    memory_key: str, memory_value: str, operation: str, metadata: dict = None
):
    """Log context memory operations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO context_memory_log (memory_key, memory_value, operation, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            memory_key,
            memory_value,
            operation,
            json.dumps(metadata or {}),
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_context_memory_logs(limit: int = 50):
    """Get recent context memory logs."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM context_memory_log ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    init_database()
    print("\n[DB] Tables:", get_all_tables())
    print("\n[DB] Sample query:")
    result = get_table_data("orders")
    print(f"  {len(result['data'])} orders found")
