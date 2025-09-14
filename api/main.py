# api/main.py
import asyncio, re
from collections import Counter
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg2.extras

from scanner.crawler import run_scan
from scanner.detector import detect
from scanner.db import (
    get_conn,
    upsert_website,
    insert_detection,
    fetch_websites,
    fetch_website,
)

# Load env variables if present
load_dotenv()

app = FastAPI(title="Website Tech Snapshot API")

# Allow React frontend on port 3001
origins = ["http://localhost:3001", "http://127.0.0.1:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class ScanRequest(BaseModel):
    domain: str


# --- Helpers ---
def get_title(html: str) -> str | None:
    """Extract the <title> tag from HTML."""
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    return m.group(1).strip() if m else None


# --- Routes ---
@app.post("/api/scan")
async def api_scan(req: ScanRequest):
    """Scan a single domain, detect stack, store in DB."""
    domain = req.domain.strip()
    if not domain:
        raise HTTPException(status_code=400, detail="domain required")

    results = await run_scan([domain], concurrency=1)
    res = results[0]

    url = res.get("url") or f"https://{domain}"

    if res.get("ok"):
        html = res["text"]
        title = get_title(html)
        detected = detect(html, url)

        # Normalize lists
        detected["cms"] = detected.get("cms") or []
        detected["js_libs"] = detected.get("js_libs") or []
        detected["analytics"] = detected.get("analytics") or []
        detected["custom_tags"] = detected.get("custom_tags") or []

        def save_success():
            conn = get_conn()
            wid = upsert_website(conn, domain, url, "ok", res.get("status"), title)
            insert_detection(
                conn,
                wid,
                detected["cms"],
                detected["js_libs"],
                detected["analytics"],
                detected["custom_tags"],
                detected.get("raw"),
            )
            conn.close()
            return wid

        wid = await asyncio.to_thread(save_success)

        return {
            "domain": domain,
            "url": url,
            "status": "ok",
            "detected": detected,
            "website_id": wid,
        }

    else:
        error_msg = res.get("error", "Unknown fetch error")

        def save_error():
            conn = get_conn()
            wid = upsert_website(conn, domain, url, "error", res.get("status"), None)
            insert_detection(conn, wid, [], [], [], [], {"error": error_msg})
            conn.close()
            return wid

        wid = await asyncio.to_thread(save_error)

        # Don’t just throw 502 → return structured response
        return {
            "domain": domain,
            "url": url,
            "status": "error",
            "error": error_msg,
            "website_id": wid,
            "detected": {
                "cms": [],
                "js_libs": [],
                "analytics": [],
                "custom_tags": [],
                "raw": {"error": error_msg},
            },
        }


@app.get("/api/websites")
async def api_list_websites(
    page: int = 1,
    per_page: int = 50,
    js_libs: str | None = Query(None),
    cms: str | None = Query(None),
):
    """List websites with latest detections (with filters)."""
    js_list = js_libs.split(",") if js_libs else None
    cms_list = cms.split(",") if cms else None
    offset = (page - 1) * per_page

    rows = await asyncio.to_thread(
        fetch_websites, per_page, offset, js_list, cms_list
    )
    return {"items": rows, "page": page, "per_page": per_page}


@app.get("/api/websites/{domain}")
async def api_get_website(domain: str):
    """Get the latest detection for one website."""
    row = await asyncio.to_thread(fetch_website, domain)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return row


@app.get("/api/websites/latest")
async def api_latest_websites(limit: int = 20):
    """Return the most recent detections (for dashboard table)."""

    def fetch_latest():
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT w.domain, d.cms, d.js_libs, d.analytics, d.custom_tags, d.detected_at, w.status
            FROM websites w
            JOIN detections d ON w.id = d.website_id
            ORDER BY d.detected_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    return await asyncio.to_thread(fetch_latest)


@app.get("/api/stats")
async def api_stats():
    """Aggregate counts for CMS, JS libs, analytics, and ads pixels."""

    def fetch_stats():
        conn = get_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        stats = {"cms": [], "js_libs": [], "analytics": [], "ads_pixels": []}
        fields = ["cms", "js_libs", "analytics", "custom_tags"]

        for field in fields:
            cur.execute(f"SELECT {field} FROM detections")
            rows = cur.fetchall()
            counter = Counter()
            for row in rows:
                items = row[field] or []
                if isinstance(items, list):
                    counter.update(items)
            stats[field] = [
                {"name": k, "count": v} for k, v in counter.most_common(10)
            ]

        conn.close()
        # rename custom_tags → ads_pixels
        stats["ads_pixels"] = stats.pop("custom_tags")
        return stats

    return await asyncio.to_thread(fetch_stats)


@app.get("/api/health")
async def health():
    """Simple health check."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Landing page."""
    return {
        "message": "Welcome to Website Tech Snapshot API",
        "docs": "/docs",
        "endpoints": [
            "/api/scan",
            "/api/websites",
            "/api/websites/{domain}",
            "/api/websites/latest",
            "/api/stats",
            "/api/health",
        ],
    }
