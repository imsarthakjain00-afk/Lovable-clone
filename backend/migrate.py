from src.utils.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS generated_html TEXT"))
    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS design_id VARCHAR"))
    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS generation_count INTEGER NOT NULL DEFAULT 0"))
    conn.commit()
    print("Migration successful — columns added.")
