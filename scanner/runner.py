import os
import time
import asyncio
import tldextract
from dotenv import load_dotenv

from scanner.crawler import run_scan
from scanner.detector import detect, get_company
from scanner.db import get_conn, upsert_website, insert_detection

load_dotenv()

DOMAINS_FILE = os.getenv("DOMAINS_FILE", "domains.txt")


def normalize_domain(d: str) -> str:
    """Ensure domain is normalized (no scheme, no extra path)."""
    e = tldextract.extract(d)
    return ".".join([e.domain, e.suffix]) if not e.subdomain else ".".join([e.subdomain, e.domain, e.suffix])


async def scan_domains(domains: list[str]):
    results = await run_scan(domains, concurrency=3)

    for res in results:
        domain = res["domain"]
        url = res.get("url") or f"https://{domain}"

        try:
            if res.get("ok"):
                html = res["text"]

                # WHOIS org lookup
                company_name = get_company(domain)

                # Run detection
                detected = detect(html, res.get("headers", {}))

                # Save to DB
                def save_success():
                    conn = get_conn()
                    wid = upsert_website(conn, domain, url, "ok", res.get("status"), None)
                    insert_detection(
                        conn,
                        wid,
                        detected["cms"],
                        detected["js_libs"],
                        detected["analytics"],
                        detected["custom_tags"],
                        detected,
                    )
                    conn.close()
                    return wid

                wid = await asyncio.to_thread(save_success)
                print(f"🌍 {domain} ✅ Detected {len(detected['raw'])} techs → Website ID {wid}")

            else:
                error_msg = res.get("error", "Unknown fetch error")

                def save_error():
                    conn = get_conn()
                    wid = upsert_website(conn, domain, url, "error", res.get("status"), None)
                    insert_detection(conn, wid, [], [], [], [], {"error": error_msg})
                    conn.close()
                    return wid

                wid = await asyncio.to_thread(save_error)
                print(f"🌍 {domain} ❌ Error: {error_msg} → Website ID {wid}")

        except Exception as e:
            print(f"❌ Error handling {domain}: {e}")

        time.sleep(1)  # avoid hammering


def main():
    if not os.path.exists(DOMAINS_FILE):
        print(f"❌ Domains file {DOMAINS_FILE} not found.")
        return

    with open(DOMAINS_FILE, "r") as f:
        domains = [normalize_domain(line.strip()) for line in f if line.strip()]

    print(f"🚀 Starting batch scan for {len(domains)} domains")
    asyncio.run(scan_domains(domains))
    print("✅ All scans complete.")


if __name__ == "__main__":
    main()
