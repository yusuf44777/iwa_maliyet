"""
SQLite -> PostgreSQL veri taşıma scripti.

Kullanım:
  DATABASE_URL='postgresql://...'
  python migrate_sqlite_to_postgres.py [sqlite_db_path]
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

from database import adapt_sql_for_backend, get_db, init_db

try:
    from psycopg2.extras import execute_batch
except Exception:
    execute_batch = None


TABLES_IN_ORDER = [
    "products",
    "raw_materials",
    "cost_definitions",
    "users",
    "product_materials",
    "product_costs",
    "audit_logs",
]


def load_sqlite_rows(sqlite_conn: sqlite3.Connection, table: str):
    sqlite_conn.row_factory = sqlite3.Row
    rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
    return [dict(r) for r in rows]


def batched(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def migrate(sqlite_path: Path):
    if not os.getenv("DATABASE_URL", "").strip():
        raise RuntimeError("DATABASE_URL tanımlı değil. PostgreSQL URL verin.")
    if not sqlite_path.exists():
        raise RuntimeError(f"SQLite dosyası bulunamadı: {sqlite_path}")

    # PG tarafında tabloları hazırla
    init_db()
    pg = get_db()

    # Hedefi temizle
    joined = ", ".join(TABLES_IN_ORDER)
    pg.execute(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE")
    pg.commit()

    sqlite_conn = sqlite3.connect(str(sqlite_path))

    total = 0
    batch_size = max(100, int(os.getenv("MIGRATION_BATCH_SIZE", "1000")))
    print(f"Batch size: {batch_size}")
    for table in TABLES_IN_ORDER:
        rows = load_sqlite_rows(sqlite_conn, table)
        if not rows:
            print(f"- {table}: 0 satır")
            continue

        cols = list(rows[0].keys())
        col_sql = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(cols))
        insert_sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})"
        insert_sql = adapt_sql_for_backend(insert_sql)
        values = [tuple(row.get(c) for c in cols) for row in rows]
        table_total = len(values)
        inserted = 0
        cursor = pg.cursor()
        raw_cursor = getattr(cursor, "_inner", cursor)

        for chunk in batched(values, batch_size):
            if execute_batch is not None:
                execute_batch(raw_cursor, insert_sql, chunk, page_size=len(chunk))
            else:
                raw_cursor.executemany(insert_sql, chunk)

            inserted += len(chunk)
            total += len(chunk)
            if inserted == table_total or inserted % batch_size == 0:
                print(f"  {table}: {inserted}/{table_total}")

        # id sequence'leri MAX(id)'ye çek
        if "id" in cols:
            pg.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence(?, 'id'),
                    COALESCE((SELECT MAX(id) FROM """ + table + """), 1),
                    (SELECT COUNT(*) > 0 FROM """ + table + """)
                )
                """,
                (table,),
            )

        pg.commit()
        print(f"- {table}: {table_total} satır")

    pg.close()
    sqlite_conn.close()
    print(f"✅ Migration tamamlandı. Toplam {total} satır taşındı.")


if __name__ == "__main__":
    default_sqlite = Path(__file__).resolve().parent / "maliyet.db"
    sqlite_arg = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else default_sqlite
    migrate(sqlite_arg)
