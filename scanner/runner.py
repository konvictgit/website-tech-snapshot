import os
import time
import tldextract
import requests
import psycopg2
from dotenv import load_dotenv
from scanner.detector import get_company
  # WHOIS-based company lookup

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://mixrank:mixrankpass@localhost:5432/mixrank_mini")
DOMAINS_FILE = os.getenv("DOMAINS_FILE", "domains.txt")
HEADERS = {"User-Agent": "MiniMixRankBot/1.0 (+https://example.com)"}


# --- Extended Technology Patterns (~100) with categories ---
TECH_PATTERNS = {
    # CMS
    "WordPress": (["wp-content", "wordpress"], "CMS"),
    "Drupal": (["drupal"], "CMS"),
    "Joomla": (["joomla"], "CMS"),
    "Magento": (["magento"], "CMS"),
    "Shopify": (["cdn.shopify.com", "shopify"], "CMS"),
    "Ghost": (["ghost"], "CMS"),
    "Squarespace": (["squarespace"], "CMS"),
    "Wix": (["wixstatic"], "CMS"),
    "HubSpot CMS": (["hubspot"], "CMS"),

    # JavaScript Frameworks
    "React": (["data-reactroot", "react"], "JavaScript Framework"),
    "Angular": (["angular"], "JavaScript Framework"),
    "Vue.js": (["vue"], "JavaScript Framework"),
    "Next.js": (["_next"], "JavaScript Framework"),
    "Nuxt.js": (["nuxt"], "JavaScript Framework"),
    "Svelte": (["svelte"], "JavaScript Framework"),
    "Ember.js": (["ember"], "JavaScript Framework"),
    "jQuery": (["jquery"], "JavaScript Framework"),
    "Backbone.js": (["backbone"], "JavaScript Framework"),

    # UI Frameworks
    "Bootstrap": (["bootstrap"], "UI Framework"),
    "Tailwind CSS": (["tailwind"], "UI Framework"),
    "Material UI": (["mui", "material-ui"], "UI Framework"),
    "Ant Design": (["ant-design"], "UI Framework"),

    # Analytics
    "Google Analytics": (["googletagmanager", "analytics.js", "gtag("], "Analytics"),
    "Facebook Pixel": (["fbq("], "Analytics"),
    "Hotjar": (["hotjar"], "Analytics"),
    "Mixpanel": (["mixpanel"], "Analytics"),
    "Segment": (["segment"], "Analytics"),
    "Amplitude": (["amplitude"], "Analytics"),
    "Heap": (["heapanalytics"], "Analytics"),
    "Matomo": (["matomo", "piwik"], "Analytics"),
    "Adobe Analytics": (["omniture", "adobeanalytics"], "Analytics"),

    # Payments
    "Stripe": (["stripe"], "Payments"),
    "PayPal": (["paypal"], "Payments"),
    "Square": (["squareup"], "Payments"),
    "Braintree": (["braintree"], "Payments"),
    "Razorpay": (["razorpay"], "Payments"),
    "Adyen": (["adyen"], "Payments"),

    # Hosting/CDN
    "Cloudflare": (["cloudflare"], "Hosting/CDN"),
    "Akamai": (["akamai"], "Hosting/CDN"),
    "Fastly": (["fastly"], "Hosting/CDN"),
    "AWS CloudFront": (["cloudfront"], "Hosting/CDN"),
    "Netlify": (["netlify"], "Hosting/CDN"),
    "Vercel": (["vercel"], "Hosting/CDN"),
    "Firebase Hosting": (["firebaseapp"], "Hosting/CDN"),
    "Heroku": (["herokucdn"], "Hosting/CDN"),
    "Google Cloud": (["gstatic"], "Hosting/CDN"),
    "Azure": (["azure"], "Hosting/CDN"),

    # Backends
    "PHP": ([".php"], "Backend"),
    "ASP.NET": (["asp.net"], "Backend"),
    "Ruby on Rails": (["rails"], "Backend"),
    "Django": (["django"], "Backend"),
    "Flask": (["flask"], "Backend"),
    "Laravel": (["laravel"], "Backend"),
    "Spring": (["spring"], "Backend"),
    "Express.js": (["express"], "Backend"),
    "Symfony": (["symfony"], "Backend"),
}


# --- DB helpers ---
def connect_db():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def ensure_tech_exists(conn, name, category=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO technologies (name, category)
            VALUES (%s, %s)
            ON CONFLICT (name) DO NOTHING
        """, (name, category))
        cur.execute("SELECT id FROM technologies WHERE name=%s", (name,))
        r = cur.fetchone()
        return r[0] if r else None


def upsert_website(conn, domain, url=None, company_name=None, hosting=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO websites (domain, url, company_name, hosting, last_scanned)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (domain) DO UPDATE
              SET url = EXCLUDED.url,
                  company_name = EXCLUDED.company_name,
                  hosting = EXCLUDED.hosting,
                  last_scanned = now()
            RETURNING id
        """, (domain, url, company_name, hosting))
        return cur.fetchone()[0]


def link_website_tech(conn, website_id, tech_id):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO website_technologies (website_id, technology_id, detected_at)
            VALUES (%s, %s, now())
            ON CONFLICT DO NOTHING
        """, (website_id, tech_id))


# --- Detection ---
def detect_fallback(html, headers=None):
    found = []
    low = html.lower()
    headers_text = " ".join([str(v).lower() for v in headers.values()]) if headers else ""

    for name, (patterns, category) in TECH_PATTERNS.items():
        for p in patterns:
            # ✅ Safe substring check instead of regex
            if p.lower() in low or p.lower() in headers_text:
                found.append((name, category))
                break
    return list(set(found))


def fetch_html(domain):
    url = domain if domain.startswith("http") else f"https://{domain}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        return r.text, r.url, r.headers
    except Exception:
        try:
            r = requests.get(url.replace("https://", "http://"), headers=HEADERS, timeout=15)
            return r.text, r.url, r.headers
        except Exception as e2:
            print(f"Failed to fetch {domain}: {e2}")
            return "", None, {}


def normalize_domain(d):
    e = tldextract.extract(d)
    if e.subdomain:
        return ".".join([e.subdomain, e.domain, e.suffix])
    return ".".join([e.domain, e.suffix])


# --- Main ---
def main():
    conn = connect_db()
    print("✅ Connected to DB")

    # Pre-seed all known techs
    for t, (_, cat) in TECH_PATTERNS.items():
        ensure_tech_exists(conn, t, cat)

    domains_path = os.path.join(os.getcwd(), DOMAINS_FILE)
    if not os.path.exists(domains_path):
        print(f"❌ Domains file {domains_path} missing.")
        return

    with open(domains_path, "r") as f:
        domains = [line.strip() for line in f if line.strip()]

    for domain in domains:
        try:
            nd = normalize_domain(domain)
            print(f"\n🌍 Scanning {nd} ...")
            html, final_url, headers = fetch_html(nd)
            if not html:
                print("⚠️ No HTML retrieved")
                continue

            # WHOIS company
            company_name = get_company(nd) or "-"

            # Hosting provider from headers
            hosting = headers.get("Server") or headers.get("X-Powered-By") or "-"

            print(f"🏢 Company: {company_name} | ☁️ Hosting: {hosting}")

            # Insert/Update website row
            website_id = upsert_website(conn, nd, final_url, company_name, hosting)

            # Detect technologies
            detected = detect_fallback(html, headers)
            print("🔎 Detected:", [d[0] for d in detected])

            for tname, cat in detected:
                tech_id = ensure_tech_exists(conn, tname, cat)
                if tech_id:
                    link_website_tech(conn, website_id, tech_id)

            time.sleep(1)  # avoid hammering
        except Exception as e:
            print("❌ Error scanning", domain, e)

    conn.close()
    print("✅ Scan complete.")


if __name__ == "__main__":
    main()
