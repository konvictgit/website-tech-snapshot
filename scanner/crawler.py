# scanner/crawler.py
import asyncio
import aiohttp
from bs4 import BeautifulSoup

from scanner.detector import detect_technologies, get_company
from scanner.db import get_conn, upsert_website, insert_detection

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MiniMixRankBot/1.0)"}


async def fetch_html(session, url):
    """Fetch HTML content for a given URL asynchronously."""
    try:
        async with session.get(url, headers=HEADERS, timeout=15) as resp:
            text = await resp.text(errors="ignore")
            return {
                "ok": resp.status == 200,
                "status": resp.status,
                "url": str(resp.url),
                "text": text,
            }
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url, "status": None}


async def process_domain(session, domain):
    """Process a single domain: fetch, detect tech, save to DB."""
    url = domain if domain.startswith("http") else f"https://{domain}"
    result = await fetch_html(session, url)

    if result["ok"]:
        html = result["text"]

        # detect techs from HTML + headers
        detected = detect_technologies(html, {"url": result["url"]})

        # company from WHOIS
        company = get_company(domain)

        # save results in DB
        conn = get_conn()
        wid = upsert_website(conn, domain, result["url"], "ok", result["status"], None)
        insert_detection(conn, wid, detected, [], [], [], {"company": company})
        conn.close()

        return {
            "domain": domain,
            "url": result["url"],
            "ok": True,
            "status": result["status"],
            "detected": detected,
        }

    else:
        # error case, log to DB as failed detection
        conn = get_conn()
        wid = upsert_website(conn, domain, url, "error", result.get("status"), None)
        insert_detection(conn, wid, [], [], [], [], {"error": result.get("error")})
        conn.close()

        return {
            "domain": domain,
            "url": url,
            "ok": False,
            "status": result.get("status"),
            "error": result.get("error"),
        }


async def run_scan(domains, concurrency=3):
    """Run parallel scans for a list of domains."""
    connector = aiohttp.TCPConnector(limit_per_host=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [process_domain(session, d) for d in domains]
        results = await asyncio.gather(*tasks)
    return results
