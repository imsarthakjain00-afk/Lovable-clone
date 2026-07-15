"""
Full schema sync — checks every column defined in every SQLAlchemy model
against what actually exists in the live PostgreSQL database.
Missing columns are added automatically with ALTER TABLE ... ADD COLUMN IF NOT EXISTS.
"""
from sqlalchemy import inspect, text, Integer, String, Text, BigInteger, Boolean
from src.utils.db import engine, Base

# Import all models so they are registered on Base.metadata
import src.Users.models          # noqa: F401
import src.Projects.models       # noqa: F401

# ── Mapping from SQLAlchemy type classes → Postgres DDL type strings ──────────
def pg_type(col):
    t = type(col.type)
    if t.__name__ in ("Integer", "INT"):        return "INTEGER"
    if t.__name__ == "BigInteger":              return "BIGINT"
    if t.__name__ in ("String", "VARCHAR"):     return "VARCHAR"
    if t.__name__ in ("Text",):                 return "TEXT"
    if t.__name__ == "Boolean":                 return "BOOLEAN"
    if t.__name__ in ("JSON", "JSONB"):         return "JSONB"
    if t.__name__ in ("DateTime",):             return "TIMESTAMPTZ"
    return "TEXT"   # safe fallback

insp = inspect(engine)
all_tables = {t.name: t for t in Base.metadata.sorted_tables}

results = []
with engine.connect() as conn:
    for table_name, table in all_tables.items():
        db_cols = {c["name"] for c in insp.get_columns(table_name)}
        model_cols = {c.name: c for c in table.columns}

        for col_name, col in model_cols.items():
            if col_name not in db_cols:
                ddl_type = pg_type(col)
                sql = f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {ddl_type};"
                conn.execute(text(sql))
                results.append(f"  ADDED  {table_name}.{col_name}  ({ddl_type})")
            else:
                results.append(f"  OK     {table_name}.{col_name}")

    conn.commit()

print("\n=== Schema Sync Report ===")
for r in results:
    print(r)
print(f"\nTotal: {len(results)} columns checked. Done.")
