# scanner/detector.py
import re
import whois

TECH_PATTERNS = {
    "WordPress": re.compile(r"wp-content|wordpress", re.I),
    "Drupal": re.compile(r"drupal", re.I),
    "Joomla": re.compile(r"joomla", re.I),
    "Shopify": re.compile(r"shopify", re.I),
    "React": re.compile(r"react", re.I),
    "Vue.js": re.compile(r"vue(\.js)?", re.I),
    "Angular": re.compile(r"angular", re.I),
    "Next.js": re.compile(r"_next", re.I),
    "Svelte": re.compile(r"svelte", re.I),
    "Ember.js": re.compile(r"ember", re.I),
    "jQuery": re.compile(r"jquery", re.I),
    "Bootstrap": re.compile(r"bootstrap", re.I),
    "Tailwind CSS": re.compile(r"tailwind", re.I),
    "Google Analytics": re.compile(r"googletagmanager|analytics\.js|gtag\(", re.I),
    "Stripe": re.compile(r"stripe", re.I),
    "PayPal": re.compile(r"paypal", re.I),
    "Cloudflare": re.compile(r"cloudflare", re.I),
    "Akamai": re.compile(r"akamai", re.I),
    "Fastly": re.compile(r"fastly", re.I),
    "PHP": re.compile(r"\.php", re.I),
    "Django": re.compile(r"django", re.I),
    "Flask": re.compile(r"flask", re.I),
    "Laravel": re.compile(r"laravel", re.I),
}


def detect(html: str, headers: dict | None = None) -> dict:
    """Return structured detection result."""
    found = []
    for name, pattern in TECH_PATTERNS.items():
        if pattern.search(html) or (headers and any(pattern.search(str(v)) for v in headers.values())):
            found.append(name)

    return {
        "cms": [t for t in found if t in ["WordPress", "Drupal", "Joomla", "Shopify"]],
        "js_libs": [t for t in found if t in ["React", "Vue.js", "Angular", "Next.js", "Svelte", "Ember.js", "jQuery"]],
        "analytics": [t for t in found if t in ["Google Analytics"]],
        "custom_tags": [t for t in found if t in ["Stripe", "PayPal", "Cloudflare", "Akamai", "Fastly"]],
        "raw": found,
    }


# alias so crawler.py and api/main.py can both use detect_technologies()
def detect_technologies(html: str, headers: dict | None = None) -> list[str]:
    """Flat list of detected technologies (wrapper for detect)."""
    result = detect(html, headers)
    return result["raw"]


def get_company(domain: str) -> str:
    """Try WHOIS lookup for company/org name."""
    try:
        w = whois.whois(domain)
        for field in ["org", "registrant_org", "registrant_name", "registrant_company", "name"]:
            val = w.get(field)
            if isinstance(val, list):
                val = val[0]
            if isinstance(val, str) and val.strip() and "REDACTED" not in val.upper():
                return val.strip()
    except Exception as e:
        print(f"[!] WHOIS error for {domain}: {e}")
    return "-"
