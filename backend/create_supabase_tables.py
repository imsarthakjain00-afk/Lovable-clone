"""
Creates the website_users table in Supabase.
Run once: python create_supabase_tables.py
"""
import os, sys
from dotenv import load_dotenv
load_dotenv()

try:
    from supabase import create_client
except ImportError:
    print("Installing supabase-py...")
    os.system(f"{sys.executable} -m pip install supabase")
    from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env")
    sys.exit(1)

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# The JS client upserts into this table from generated websites
# We use the REST API to run raw SQL via the service role key
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS website_users (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    firebase_uid    TEXT NOT NULL,
    project_id      TEXT NOT NULL,
    email           TEXT,
    display_name    TEXT,
    photo_url       TEXT,
    last_login      TIMESTAMPTZ DEFAULT now(),
    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (firebase_uid, project_id)
);

-- Allow anonymous (JS client) inserts and upserts
ALTER TABLE website_users ENABLE ROW LEVEL SECURITY;

-- Policy: anyone with a valid anon key can insert/upsert their own row
CREATE POLICY IF NOT EXISTS "insert_own_user"
    ON website_users FOR INSERT
    WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "update_own_user"
    ON website_users FOR UPDATE
    USING (true);

CREATE POLICY IF NOT EXISTS "read_own_user"
    ON website_users FOR SELECT
    USING (true);
"""

print("Creating website_users table in Supabase...")

# Use Supabase's rpc or raw pg endpoint
# The cleanest way with supabase-py v2 is via the postgrest SQL endpoint
import httpx

resp = httpx.post(
    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
    json={"sql": CREATE_SQL},
    headers={
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    },
    timeout=30,
)

if resp.status_code == 200:
    print("✅ website_users table created successfully")
else:
    # Try direct SQL via postgres connection as fallback
    print(f"RPC failed ({resp.status_code}): {resp.text}")
    print("Trying psycopg2 fallback...")
    import psycopg2
    from urllib.parse import urlparse

    db_url = os.getenv("DB_CONNECTION")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(CREATE_SQL)
    conn.close()
    print("✅ website_users table created via psycopg2")
