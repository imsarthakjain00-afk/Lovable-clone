"""
HTML File Splitter + Project Manifest Builder
=============================================
Takes the monolithic generated HTML and produces a full virtual
multi-file project structure for display in the Code Explorer:

  index.html                       — full page (source of truth for preview)
  styles.css                       — extracted <style> blocks
  app.js                           — extracted inline <script> blocks
  supabase/migrations/001_init.sql — always: website_users table + RLS
  supabase/migrations/002_app.sql  — dynamic: tables derived from HTML features
  README.md                        — project setup guide
"""
import re
from typing import Dict


# ─────────────────────────────────────────────────────────────────────────────
# HTML parsing
# ─────────────────────────────────────────────────────────────────────────────

def _extract_css(html: str) -> str:
    blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
    return "\n\n".join(b.strip() for b in blocks if b.strip())


def _extract_js(html: str) -> str:
    # Only inline scripts (no src= attribute)
    blocks = re.findall(
        r'<script(?![^>]*\bsrc\s*=)[^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    )
    # Skip injected platform scripts (Firebase / Supabase bootstrap)
    skip_markers = ["firebase.initializeApp", "supabase.createClient", "Lovable] Firebase Auth ready"]
    result = []
    for b in blocks:
        b = b.strip()
        if b and not any(m in b for m in skip_markers):
            result.append(b)
    return "\n\n".join(result)


def _clean_html(html: str) -> str:
    h = html.strip()
    if h.startswith("```"):
        h = re.sub(r'^```(html)?\s*', '', h, flags=re.IGNORECASE)
        h = re.sub(r'\s*```\s*$', '', h)
    return h.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Feature detection (what does this website actually need?)
# ─────────────────────────────────────────────────────────────────────────────

def _detect_features(html: str) -> Dict[str, bool]:
    h = html.lower()
    return {
        "auth":      any(k in h for k in ["signinwithgoogle", "signinwithemail", "signupwithemail", "login", "sign in", "sign up", "register"]),
        "ecommerce": any(k in h for k in ["add to cart", "buy now", "checkout", "product", "price", "shop"]),
        "blog":      any(k in h for k in ["blog", "post", "article", "read more"]),
        "contact":   any(k in h for k in ["contact", "get in touch", "send message", "your message"]),
        "booking":   any(k in h for k in ["book", "appointment", "reserve", "schedule"]),
        "reviews":   any(k in h for k in ["review", "testimonial", "rating", "stars"]),
        "newsletter":any(k in h for k in ["newsletter", "subscribe", "email list"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# SQL migration generators
# ─────────────────────────────────────────────────────────────────────────────

MIGRATION_001 = """\
-- ═══════════════════════════════════════════════════════════════
-- Migration 001: Core authentication table
-- Stores visitors who sign in via Firebase Auth on this website
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS website_users (
    id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    firebase_uid  TEXT        NOT NULL,
    project_id    TEXT        NOT NULL,
    email         TEXT,
    display_name  TEXT,
    photo_url     TEXT,
    last_login    TIMESTAMPTZ DEFAULT now(),
    created_at    TIMESTAMPTZ DEFAULT now(),
    UNIQUE (firebase_uid, project_id)
);

-- Row Level Security
ALTER TABLE website_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS "website_users_insert"
    ON website_users FOR INSERT WITH CHECK (true);

CREATE POLICY IF NOT EXISTS "website_users_update"
    ON website_users FOR UPDATE USING (true);

CREATE POLICY IF NOT EXISTS "website_users_select"
    ON website_users FOR SELECT USING (true);
"""


def _build_migration_002(features: Dict[str, bool], project_id: int) -> str:
    blocks = [
        "-- ═══════════════════════════════════════════════════════════════",
        f"-- Migration 002: Application tables for project {project_id}",
        "-- ═══════════════════════════════════════════════════════════════",
        "",
    ]

    if features["ecommerce"]:
        blocks += [
            "-- Products catalogue",
            "CREATE TABLE IF NOT EXISTS products (",
            "    id          UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id  TEXT    NOT NULL,",
            "    name        TEXT    NOT NULL,",
            "    description TEXT,",
            "    price       NUMERIC(10,2),",
            "    image_url   TEXT,",
            "    stock       INT     DEFAULT 0,",
            "    created_at  TIMESTAMPTZ DEFAULT now()",
            ");",
            "",
            "-- Shopping cart / orders",
            "CREATE TABLE IF NOT EXISTS orders (",
            "    id             UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id     TEXT    NOT NULL,",
            "    firebase_uid   TEXT    NOT NULL,",
            "    items          JSONB   DEFAULT '[]',",
            "    total          NUMERIC(10,2),",
            "    status         TEXT    DEFAULT 'pending',",
            "    created_at     TIMESTAMPTZ DEFAULT now()",
            ");",
            "",
        ]

    if features["contact"]:
        blocks += [
            "-- Contact form submissions",
            "CREATE TABLE IF NOT EXISTS contact_messages (",
            "    id          UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id  TEXT    NOT NULL,",
            "    name        TEXT,",
            "    email       TEXT,",
            "    message     TEXT,",
            "    created_at  TIMESTAMPTZ DEFAULT now()",
            ");",
            "",
        ]

    if features["blog"]:
        blocks += [
            "-- Blog / articles",
            "CREATE TABLE IF NOT EXISTS blog_posts (",
            "    id          UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id  TEXT    NOT NULL,",
            "    title       TEXT    NOT NULL,",
            "    content     TEXT,",
            "    author_uid  TEXT,",
            "    published   BOOL    DEFAULT false,",
            "    created_at  TIMESTAMPTZ DEFAULT now()",
            ");",
            "",
        ]

    if features["booking"]:
        blocks += [
            "-- Appointment / booking slots",
            "CREATE TABLE IF NOT EXISTS bookings (",
            "    id           UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id   TEXT    NOT NULL,",
            "    firebase_uid TEXT,",
            "    name         TEXT,",
            "    email        TEXT,",
            "    slot         TIMESTAMPTZ,",
            "    notes        TEXT,",
            "    status       TEXT    DEFAULT 'pending',",
            "    created_at   TIMESTAMPTZ DEFAULT now()",
            ");",
            "",
        ]

    if features["reviews"]:
        blocks += [
            "-- Customer reviews / testimonials",
            "CREATE TABLE IF NOT EXISTS reviews (",
            "    id           UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id   TEXT    NOT NULL,",
            "    firebase_uid TEXT,",
            "    reviewer     TEXT,",
            "    rating       INT     CHECK (rating BETWEEN 1 AND 5),",
            "    body         TEXT,",
            "    created_at   TIMESTAMPTZ DEFAULT now()",
            ");",
            "",
        ]

    if features["newsletter"]:
        blocks += [
            "-- Newsletter subscriptions",
            "CREATE TABLE IF NOT EXISTS newsletter_subscribers (",
            "    id          UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id  TEXT    NOT NULL,",
            "    email       TEXT    NOT NULL,",
            "    created_at  TIMESTAMPTZ DEFAULT now(),",
            "    UNIQUE (project_id, email)",
            ");",
            "",
        ]

    # If no feature-specific tables, add a generic app_data store
    has_tables = any([
        features["ecommerce"], features["contact"], features["blog"],
        features["booking"], features["reviews"], features["newsletter"]
    ])
    if not has_tables:
        blocks += [
            "-- Generic key-value store for this project",
            "CREATE TABLE IF NOT EXISTS app_data (",
            "    id          UUID    DEFAULT gen_random_uuid() PRIMARY KEY,",
            "    project_id  TEXT    NOT NULL,",
            "    key         TEXT    NOT NULL,",
            "    value       JSONB,",
            "    created_at  TIMESTAMPTZ DEFAULT now()",
            ");",
            "",
        ]

    return "\n".join(blocks)


# ─────────────────────────────────────────────────────────────────────────────
# README
# ─────────────────────────────────────────────────────────────────────────────

def _build_readme(features: Dict[str, bool], project_id: int) -> str:
    feature_list = [k for k, v in features.items() if v]
    feature_str = ", ".join(feature_list) if feature_list else "static content"

    return f"""\
# Project {project_id} — Generated Website

Built with **Lovable Clone** AI Website Builder.

## Tech Stack
| Layer       | Technology |
|-------------|------------|
| Frontend    | HTML5 + Tailwind CSS |
| Auth        | Firebase Authentication (Google + Email/Password) |
| Database    | Supabase (PostgreSQL) |
| Hosting     | Vercel |

## Detected Features
{feature_str}

## Project Files
| File | Purpose |
|------|---------|
| `index.html` | Main website (entry point) |
| `styles.css` | Extracted CSS styles |
| `app.js` | Extracted JavaScript |
| `supabase/migrations/001_init.sql` | Core auth table |
| `supabase/migrations/002_app.sql` | App-specific tables |

## Authentication
Firebase Auth is pre-configured. Available helpers in any JS:
```js
signInWithGoogle()                      // Google OAuth popup
signInWithEmail(email, password)        // Email login
signUpWithEmail(email, password, name)  // Create account
signOutUser()                           // Sign out
getCurrentUser()                        // Get current user (or null)
window.supabaseDb                       // Supabase client for data queries
```

## Running Migrations
```sql
-- Run in Supabase SQL editor:
-- supabase/migrations/001_init.sql  (first)
-- supabase/migrations/002_app.sql   (second)
```

## Deployment
Deployed automatically to Vercel via the **Publish** button.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Multi-page extractor
# ─────────────────────────────────────────────────────────────────────────────

def _extract_pages(html: str) -> Dict[str, str]:
    """
    For multi-page sites, extracts each <section data-page="..."> block
    into a separate virtual HTML file (home.html, about.html, etc.).
    Returns {} if no page-sections found (single-page site).
    """
    sections = re.findall(
        r'(<section[^>]+data-page=["\']([^"\']+)["\'][^>]*>.*?</section>)',
        html, re.DOTALL | re.IGNORECASE
    )
    if not sections:
        return {}

    # Extract shared shell (head + nav) to wrap each standalone page
    head_match  = re.search(r'(<head>.*?</head>)', html, re.DOTALL | re.IGNORECASE)
    nav_match   = re.search(r'(<nav\b[^>]*>.*?</nav>)', html, re.DOTALL | re.IGNORECASE)
    head_html   = head_match.group(1) if head_match else "<head></head>"
    nav_html    = nav_match.group(1) if nav_match else ""

    pages: Dict[str, str] = {}
    for full_section, page_id in sections:
        safe_name = re.sub(r'[^\w-]', '-', page_id.lower())
        filename  = "index.html" if safe_name in ("home", "index", "") else f"{safe_name}.html"
        pages[filename] = f"""<!DOCTYPE html>
<html lang="en">
{head_html}
<body>
{nav_html}
{full_section}
</body>
</html>"""
    return pages


# ─────────────────────────────────────────────────────────────────────────────
# Main export
# ─────────────────────────────────────────────────────────────────────────────

def split_html_into_files(html: str, project_id: int = 0) -> Dict[str, str]:
    """
    Returns a full virtual file manifest for the Code Explorer:
    { relative_path: file_content }
    """
    if not html or not html.strip():
        return {}

    clean = _clean_html(html)
    features = _detect_features(clean)

    css = _extract_css(clean)
    js  = _extract_js(clean)

    manifest: Dict[str, str] = {}

    # Core files
    manifest["index.html"] = clean
    if css:
        manifest["styles.css"] = f"/* -- Styles extracted from index.html -- */\n\n{css}"
    if js:
        manifest["app.js"] = f"// -- Scripts extracted from index.html -- //\n\n{js}"

    # Multi-page: extract each page as a separate file
    page_files = _extract_pages(clean)
    if page_files:
        # Skip index.html duplicate — already set above
        for fname, content in page_files.items():
            if fname != "index.html":
                manifest[fname] = content
        # Also include a pages/ folder copy for clarity
        for fname, content in page_files.items():
            manifest[f"pages/{fname}"] = content

    # Supabase migrations (always present)
    manifest["supabase/migrations/001_init.sql"] = MIGRATION_001
    manifest["supabase/migrations/002_app.sql"]  = _build_migration_002(features, project_id)

    # README
    manifest["README.md"] = _build_readme(features, project_id)

    return manifest

