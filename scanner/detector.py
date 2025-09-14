import re
import whois

# Extended technology patterns (~100+ common CMS, frameworks, libraries, analytics, hosting/CDN, payments)
TECH_PATTERNS = {
    # CMS
    "WordPress": re.compile(r"wp-content|wordpress", re.I),
    "Drupal": re.compile(r"drupal|drupal-settings-json", re.I),
    "Joomla": re.compile(r"joomla", re.I),
    "Wix": re.compile(r"wixstatic", re.I),
    "Squarespace": re.compile(r"squarespace", re.I),
    "Magento": re.compile(r"magento", re.I),
    "Shopify": re.compile(r"cdn.shopify.com", re.I),
    "Blogger": re.compile(r"blogger", re.I),
    "Ghost": re.compile(r"ghost", re.I),
    "TYPO3": re.compile(r"typo3", re.I),
    "Weebly": re.compile(r"weebly", re.I),
    "HubSpot CMS": re.compile(r"hubspot|hs-scriptloader", re.I),
    "Contentful": re.compile(r"contentful", re.I),
    "Strapi": re.compile(r"strapi", re.I),
    "Sanity": re.compile(r"sanity.io", re.I),

    # JavaScript frameworks
    "React": re.compile(r"react|data-reactroot", re.I),
    "Angular": re.compile(r"angular(\.js)?", re.I),
    "Vue.js": re.compile(r"vue(\.js)?", re.I),
    "Next.js": re.compile(r"_next|next-head-count", re.I),
    "Nuxt.js": re.compile(r"nuxt", re.I),
    "Svelte": re.compile(r"svelte", re.I),
    "Ember.js": re.compile(r"ember", re.I),
    "Backbone.js": re.compile(r"backbone", re.I),
    "Alpine.js": re.compile(r"alpinejs", re.I),
    "Meteor": re.compile(r"meteor", re.I),

    # UI libraries
    "Bootstrap": re.compile(r"bootstrap", re.I),
    "Tailwind CSS": re.compile(r"tailwind", re.I),
    "Material UI": re.compile(r"material-ui|mui", re.I),
    "Foundation": re.compile(r"foundation", re.I),
    "Ant Design": re.compile(r"ant-design", re.I),
    "Bulma": re.compile(r"bulma", re.I),
    "UIKit": re.compile(r"uikit", re.I),

    # JS libraries
    "jQuery": re.compile(r"jquery", re.I),
    "Lodash": re.compile(r"lodash", re.I),
    "Moment.js": re.compile(r"moment(\.js)?", re.I),
    "D3.js": re.compile(r"d3(\.js)?", re.I),
    "Chart.js": re.compile(r"chart(\.js)?", re.I),
    "Three.js": re.compile(r"three(\.js)?", re.I),
    "Leaflet": re.compile(r"leaflet", re.I),
    "GSAP": re.compile(r"gsap", re.I),

    # Analytics & tracking
    "Google Analytics": re.compile(r"googletagmanager|analytics.js|gtag\(", re.I),
    "Facebook Pixel": re.compile(r"fbq\(", re.I),
    "Hotjar": re.compile(r"hotjar", re.I),
    "Mixpanel": re.compile(r"mixpanel", re.I),
    "Segment": re.compile(r"segment", re.I),
    "Amplitude": re.compile(r"amplitude", re.I),
    "Heap": re.compile(r"heapanalytics", re.I),
    "Crazy Egg": re.compile(r"crazyegg", re.I),
    "Matomo": re.compile(r"matomo|piwik", re.I),
    "Adobe Analytics": re.compile(r"adobeanalytics|omniture", re.I),

    # Payment
    "Stripe": re.compile(r"stripe", re.I),
    "PayPal": re.compile(r"paypal", re.I),
    "Square": re.compile(r"squareup", re.I),
    "Braintree": re.compile(r"braintree", re.I),
    "Adyen": re.compile(r"adyen", re.I),
    "Razorpay": re.compile(r"razorpay", re.I),

    # Hosting/CDN
    "Cloudflare": re.compile(r"cloudflare", re.I),
    "Akamai": re.compile(r"akamai", re.I),
    "Fastly": re.compile(r"fastly", re.I),
    "Amazon CloudFront": re.compile(r"cloudfront", re.I),
    "Netlify": re.compile(r"netlify", re.I),
    "Vercel": re.compile(r"vercel", re.I),
    "Firebase Hosting": re.compile(r"firebaseapp.com", re.I),
    "Heroku": re.compile(r"herokucdn", re.I),
    "DigitalOcean": re.compile(r"digitalocean", re.I),
    "Microsoft Azure": re.compile(r"azure", re.I),
    "Google Cloud": re.compile(r"gstatic.com", re.I),
    "AWS": re.compile(r"amazonaws.com", re.I),

    # Programming languages / frameworks
    "PHP": re.compile(r"\.php", re.I),
    "ASP.NET": re.compile(r"asp\.net", re.I),
    "Ruby on Rails": re.compile(r"rails", re.I),
    "Django": re.compile(r"csrftoken|django", re.I),
    "Flask": re.compile(r"flask", re.I),
    "Laravel": re.compile(r"laravel", re.I),
    "Spring": re.compile(r"spring", re.I),
    "Express.js": re.compile(r"express", re.I),
    "FastAPI": re.compile(r"fastapi", re.I),
    "Symfony": re.compile(r"symfony", re.I),
    "CodeIgniter": re.compile(r"codeigniter", re.I),

    # Databases
    "MySQL": re.compile(r"mysql", re.I),
    "PostgreSQL": re.compile(r"postgres", re.I),
    "MongoDB": re.compile(r"mongodb", re.I),
    "Redis": re.compile(r"redis", re.I),
    "Elasticsearch": re.compile(r"elasticsearch", re.I),

    # E-commerce
    "WooCommerce": re.compile(r"woocommerce", re.I),
    "BigCommerce": re.compile(r"bigcommerce", re.I),
    "PrestaShop": re.compile(r"prestashop", re.I),
    "OpenCart": re.compile(r"opencart", re.I),
    "osCommerce": re.compile(r"oscommerce", re.I),
    "Zen Cart": re.compile(r"zencart", re.I),

    # Email & marketing
    "Mailchimp": re.compile(r"mailchimp", re.I),
    "SendGrid": re.compile(r"sendgrid", re.I),
    "Postmark": re.compile(r"postmarkapp", re.I),
    "Klaviyo": re.compile(r"klaviyo", re.I),
    "ConvertKit": re.compile(r"convertkit", re.I),

    # Security
    "reCAPTCHA": re.compile(r"recaptcha", re.I),
    "Sucuri": re.compile(r"sucuri", re.I),
    "Imperva": re.compile(r"imperva", re.I),
    "Incapsula": re.compile(r"incapsula", re.I),

    # Misc
    "Disqus": re.compile(r"disqus", re.I),
    "Typeform": re.compile(r"typeform", re.I),
    "Zendesk": re.compile(r"zendesk", re.I),
    "Intercom": re.compile(r"intercom", re.I),
    "Optimizely": re.compile(r"optimizely", re.I),
    "New Relic": re.compile(r"newrelic", re.I),
    "Datadog": re.compile(r"datadog", re.I),
    "Sentry": re.compile(r"sentry", re.I),
}

def detect_technologies(html: str, headers: dict) -> list[str]:
    """Simple regex-based tech detection from HTML + headers."""
    found = set()

    for name, pattern in TECH_PATTERNS.items():
        if pattern.search(html) or any(pattern.search(str(v)) for v in headers.values()):
            found.add(name)

    return list(found)


def get_company(domain: str) -> str:
    """Try to get company/organization name from WHOIS data with multiple fallbacks."""
    try:
        w = whois.whois(domain)

        candidates = [
            w.get("org"),
            w.get("registrant_org"),
            w.get("registrant_name"),
            w.get("registrant_company"),
            w.get("name"),
        ]

        for c in candidates:
            if isinstance(c, list):
                c = c[0]
            if isinstance(c, str) and c.strip() and "REDACTED" not in c.upper():
                return c.strip()

    except Exception as e:
        print(f"[!] WHOIS error for {domain}: {e}")

    return "-"
