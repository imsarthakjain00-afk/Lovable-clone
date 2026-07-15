"""One-shot migration: adds deployed_url column to projects table if it doesn't exist."""
from src.utils.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS deployed_url VARCHAR;"))
    conn.commit()
    print("Migration complete — deployed_url column added.")
