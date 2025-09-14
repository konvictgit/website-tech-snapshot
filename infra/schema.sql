-- ================================
-- Websites table
-- ================================
CREATE TABLE IF NOT EXISTS websites (
    id SERIAL PRIMARY KEY,
    domain TEXT UNIQUE NOT NULL,       -- normalized domain (e.g., example.com)
    url TEXT,                          -- last resolved URL (with redirects)
    company_name TEXT,                 -- WHOIS org / registrant name
    hosting TEXT,                      -- infra provider (Cloudflare, AWS, etc.)
    last_scanned TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ================================
-- Technologies table
-- ================================
CREATE TABLE IF NOT EXISTS technologies (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,         -- e.g., "React", "WordPress"
    category TEXT                      -- e.g., CMS, Framework, Analytics
);

-- ================================
-- Scan queue
-- ================================
CREATE TABLE IF NOT EXISTS scan_queue (
    id SERIAL PRIMARY KEY,
    domain TEXT NOT NULL,
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- ================================
-- Mapping: Website ↔ Technologies
-- ================================
CREATE TABLE IF NOT EXISTS website_technologies (
    website_id INT NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    technology_id INT NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (website_id, technology_id)
);

-- ================================
-- Detections table (for db.py compatibility)
-- ================================
CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    website_id INT NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    cms TEXT[] DEFAULT '{}',
    js_libs TEXT[] DEFAULT '{}',
    analytics TEXT[] DEFAULT '{}',
    custom_tags TEXT[] DEFAULT '{}',
    raw JSONB DEFAULT '{}'::jsonb
);

-- ================================
-- Seed common technologies
-- ================================
INSERT INTO technologies (name, category) VALUES
  -- CMS / Ecommerce
  ('WordPress','CMS'),
  ('Drupal','CMS'),
  ('Joomla','CMS'),
  ('Shopify','Ecommerce'),
  ('Magento','Ecommerce'),

  -- JavaScript frameworks
  ('React','Framework'),
  ('Next.js','Framework'),
  ('Angular','Framework'),
  ('Vue.js','Framework'),
  ('Svelte','Framework'),

  -- Libraries / UI
  ('jQuery','Library'),
  ('Bootstrap','Library'),
  ('Tailwind CSS','Library'),

  -- Web servers / Caching
  ('Nginx','Web Server'),
  ('Apache','Web Server'),
  ('Varnish','Cache'),

  -- Analytics
  ('Google Analytics','Analytics'),
  ('Mixpanel','Analytics'),
  ('Hotjar','Analytics'),

  -- Payments
  ('Stripe','Payment'),
  ('PayPal','Payment'),
  ('Razorpay','Payment'),

  -- Security / Infra
  ('Cloudflare','Security'),
  ('Datadome','Security'),

  -- Hosting / Deployment
  ('Vercel','Hosting'),
  ('Netlify','Hosting'),
  ('Heroku','Hosting'),

  -- Languages / Backends
  ('PHP','Language'),
  ('Node.js','Runtime'),
  ('Ruby on Rails','Framework'),
  ('Django','Framework'),
  ('Laravel','Framework')
ON CONFLICT (name) DO NOTHING;
