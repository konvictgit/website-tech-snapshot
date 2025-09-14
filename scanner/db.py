import os
from psycopg2.extras import Json, RealDictCursor
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", os.getenv("DB_DSN", "postgresql://webtech:webtechpass@127.0.0.1:5433/webtech"))

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
    cms, js_libs, analytics, custom_tags = map(lambda x: x if isinstance(x, list) else [], [cms, js_libs, analytics, custom_tags])
    raw = raw if isinstance(raw, dict) else {}
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO detections (website_id, detected_at, cms, js_libs, analytics, custom_tags, raw)
            VALUES (%s, now(), %s, %s, %s, %s, %s)
        """, (website_id, cms, js_libs, analytics, custom_tags, Json(raw)))
    conn.commit()
