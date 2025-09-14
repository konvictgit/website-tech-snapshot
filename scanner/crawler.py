# crawler.py
import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup

# 👇 FIXED import
from scanner.detector import detect_technologies, get_company
from scanner.db import get_conn, upsert_website, insert_detection
from scanner.db import connect_db



HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MiniMixRankBot/1.0)"}

def process_domain(domain: str):
    """Fetch website, detect tech + company, save to DB."""
    print(f"[+] Processing {domain} ...")

    company = get_company(domain)
    techs = detect_technologies(domain)

    # save results in DB
    conn = connect_db()
    cur = conn.cursor()

    # insert/update website
    cur.execute(
        """
        INSERT INTO websites (domain, company_name, last_scanned)
        VALUES (%s, %s, NOW())
        ON CONFLICT (domain)
        DO UPDATE SET company_name = EXCLUDED.company_name, last_scanned = NOW()
        RETURNING id
        """,
        (domain, company),
    )
    website_id = cur.fetchone()[0]

    # insert technologies
    for tech in techs:
        cur.execute(
            "INSERT INTO technologies (name, category) VALUES (%s, 'Unknown') ON CONFLICT (name) DO NOTHING",
            (tech,),
        )
        cur.execute("SELECT id FROM technologies WHERE name=%s", (tech,))
        tech_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO website_technologies (website_id, technology_id)
            VALUES (%s, %s)
            ON CONFLICT (website_id, technology_id) DO NOTHING
            """,
            (website_id, tech_id),
        )

    conn.commit()
    cur.close()
    conn.close()

def run_crawler():
    """Pick domains from queue and process them continuously."""
    conn = connect_db()
    while True:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, domain FROM scan_queue
            WHERE processed = false
            ORDER BY id ASC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            cur.close()
            time.sleep(5)
            continue

        scan_id, domain = row
        cur.execute("UPDATE scan_queue SET processed=true WHERE id=%s", (scan_id,))
        conn.commit()
        cur.close()

        process_domain(domain)

if __name__ == "__main__":
    run_crawler()
