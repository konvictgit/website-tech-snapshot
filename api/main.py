import asyncio, re
from collections import Counter
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg2.extras

from scanner.crawler import run_scan
from scanner.detector import detect, get_company
from scanner.db import get_conn, upsert_website, insert_detection, fetch_websites, fetch_website

load_dotenv()

app = FastAPI(title="Website Tech Snapshot API")

origins = ["http://localhost:3001", "http://127.0.0.1:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    domain: str

def get_title(html: str) -> str | None:
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    return m.group(1).strip() if m else None

@app.post("/api/scan")
async def api_scan(req: ScanRequest):
    domain = req.domain.strip()
    if not domain:
        raise HTTPException(status_code=400, detail="domain required")

    results = await run_scan([domain], concurrency=1)
    res = results[0]
    url = res.get("url") or f"https://{domain}"

    if res.get("ok"):
        html = res["text"]
        title = get_title(html)
        detected = detect(html, {})

        def save_success():
            conn = get_conn()
            wid = upsert_website(conn, domain, url, "ok", res.get("status"), title)
            insert_detection(conn, wid, detected["cms"], detected["js_libs"], detected["analytics"], detected["custom_tags"], detected)
            conn.close()
            return wid

        wid = await asyncio.to_thread(save_success)
        return {"domain": domain, "url": url, "status": "ok", "detected": detected, "website_id": wid}

    else:
        error_msg = res.get("error", "Unknown fetch error")

        def save_error():
            conn = get_conn()
            wid = upsert_website(conn, domain, url, "error", res.get("status"), None)
            insert_detection(conn, wid, [], [], [], [], {"error": error_msg})
            conn.close()
            return wid

        wid = await asyncio.to_thread(save_error)
        return {"domain": domain, "url": url, "status": "error", "error": error_msg, "website_id": wid}

@app.get("/api/health")
async def health():
    return {"status": "ok"}
