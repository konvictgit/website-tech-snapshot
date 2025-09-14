# 🌐 Mini MixRank — Website Tech Snapshot

> Detect what technologies websites are built with — powered by **Python, FastAPI, PostgreSQL, Supabase, Docker, Next.js** 🚀

---

## ✨ Why this project?
- Inspired by [MixRank](https://mixrank.com/) — but a free & open-source mini version.  
- Learn how to **crawl websites** and detect **stacks** at scale.  
- Practice **real-world SaaS architecture**: scanners, backend APIs, database, frontend dashboards.  
- Showcase full-stack skills with a production-style project.  

---

## 🎥 Demo Video

➡️ [Watch the demo](https://github.com/konvictgit/website-tech-snapshot/blob/main/docs/demo.mp4?raw=true)


## 🛠️ Tech Stack  

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,fastapi,postgresql,docker,react,nextjs,vercel,github" />
</p>

- **Python** 🐍 → crawler & scanner (fetch + detect technologies)  
- **FastAPI** ⚡ → backend REST API  
- **PostgreSQL (Supabase)** 🗄️ → database for storing detections  
- **Docker & Docker Compose** 🐳 → easy orchestration (db, scanner, frontend)  
- **React / Next.js** ⚛️ → frontend dashboard  
- **Adminer** 🖥️ → database management UI  
- **Vercel** ▲ (optional) → frontend hosting  

---

## 🚀 What it does
- Crawl domains from a list.  
- Detect technologies (CMS, analytics, JavaScript libs, ads pixels).  
- Save results into PostgreSQL.  
- View everything on a clean **frontend dashboard** with graphs & tables.  
- Search domains/companies, filter by stack, get instant insights.  

---

## 📸 Demo

### Dashboard  
![screenshot](docs/dashboard.png) <!-- Add a real screenshot path -->

### Example API usage  
```bash
POST /api/scan
{
  "domain": "example.com"
}
Response:

{
  "domain": "example.com",
  "url": "https://example.com",
  "status": "ok",
  "detected": {
    "cms": ["WordPress"],
    "analytics": ["Google Analytics"],
    "js_libs": ["React"]
  },
  "website_id": 1
}
```
⚙️ Installation
1. Clone the repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>/infra

2. Setup .env (if using Supabase/Postgres)
DATABASE_URL=postgres://mixrank:mixrankpass@db:5432/mixrank_mini

3. Run with Docker Compose
docker compose up --build

4. Access services

Frontend Dashboard → http://localhost:3001

Adminer (DB UI) → http://localhost:8080

Database → exposed on port 5433

👉 Scanner runs in the background and writes to DB.
👉 API (FastAPI) can be run locally via:

uvicorn api.main:app --reload --port 9000

🌟 Why it’s wonderful

Full-stack project (backend + frontend + db + infra).

Detects real-world technologies from live websites.

Uses only free tools — easy to run on your laptop.

Production-like architecture (separate services, background worker, API, frontend).

Extensible → build dashboards, analytics, even SaaS products!

🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.
