# scanner/db.py
import os
from psycopg2.extras import Json, RealDictCursor
import psycopg2
from dotenv import load_dotenv

# load .env if present
load_dotenv()

# prefer DATABASE_URL (Supabase / Render style), fallback to DB_DSN or local
DB_URL = os.getenv(
    "DATABASE_URL",
    os.getenv("DB_DSN", "postgresql://webtech:webtechpass@127.0.0.1:5433/webtech")
)

def get_conn():
    return psycopg2.connect(DB_URL)

def upsert_website(conn, domain, url, status, http_status, title):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO websites (domain, url, last_scanned, status, http_status, title)
            VALUES (%s, %s, now(), %s, %s, %s)
            ON CONFLICT (domain) DO UPDATE SET
                url = EXCLUDED.url,
                last_scanned = now(),
                status = EXCLUDED.status,
                http_status = EXCLUDED.http_status,
                title = EXCLUDED.title
            RETURNING id;
        """, (domain, url, status, http_status, title))
        wid = cur.fetchone()[0]
    conn.commit()
    return wid

def insert_detection(conn, website_id, cms, js_libs, analytics, custom_tags, raw):
    cms = cms if isinstance(cms, list) else []
    js_libs = js_libs if isinstance(js_libs, list) else []
    analytics = analytics if isinstance(analytics, list) else []
    custom_tags = custom_tags if isinstance(custom_tags, list) else []
    raw = raw if isinstance(raw, dict) else {}

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO detections (website_id, detected_at, cms, js_libs, analytics, custom_tags, raw)
            VALUES (%s, now(), %s, %s, %s, %s, %s)
        """, (website_id, cms, js_libs, analytics, custom_tags, Json(raw)))
    conn.commit()

def fetch_websites(per_page=50, offset=0, js_libs=None, cms=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    conds = []
    params = []
    if js_libs:
        conds.append("d.js_libs @> %s")
        params.append(js_libs)
    if cms:
        conds.append("d.cms @> %s")
        params.append(cms)
    where = " AND ".join(conds)
    if where:
        where = "AND " + where
    qry = f"""
      SELECT w.domain, w.url, w.last_scanned, d.cms, d.js_libs, d.analytics, d.custom_tags
      FROM websites w
      JOIN LATERAL (
        SELECT cms, js_libs, analytics, custom_tags
        FROM detections
        WHERE website_id = w.id
        ORDER BY detected_at DESC LIMIT 1
      ) d ON true
      WHERE 1=1 {where}
      ORDER BY w.last_scanned DESC NULLS LAST
      LIMIT %s OFFSET %s;
    """
    params.extend([per_page, offset])
    cur.execute(qry, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def fetch_website(domain):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
      SELECT w.domain, w.url, w.last_scanned, d.cms, d.js_libs, d.analytics, d.custom_tags, d.raw
      FROM websites w
      JOIN detections d ON d.website_id = w.id
      WHERE w.domain = %s
      ORDER BY d.detected_at DESC
      LIMIT 1;
    """, (domain,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row
