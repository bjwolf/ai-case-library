# Canopy Refactor Plan — GSRC AI Initiatives Repository

## Overview
Migrate the current FastAPI + React (CDN) + SQLite app to Canopy-compatible
Flask/FastAPI + Jinja2 + canopy_storage + canopy_llm + canopy_auth.

---

## Step 1: Restructure Project Layout

```
app.py              ← single FastAPI entry point (port 8080, host 0.0.0.0)
requirements.txt    ← at root, pinned versions
constants.py        ← dropdown options
ranking.py          ← scoring engine
analytics.py        ← aggregation logic
agent.py            ← AI agent (upgraded to Bedrock via canopy_llm)
seed_data.py        ← initial data (runs on first startup)
templates/
├── base.html       ← dark sci-fi theme layout + inline CSS
├── browse.html     ← card view + quick filters + search
├── dashboard.html  ← stat cards + CSS charts + data table
├── leaderboard.html← ranking table + weight sliders
├── agent.html      ← chat interface
└── partials/
    ├── form_modal.html   ← initiative create/edit
    └── detail_modal.html ← read-only view
```

## Step 2: Replace SQLite with canopy_storage

- Cases stored as JSON list: storage.put_json("cases", [...])
- Roles stored as JSON dict: storage.put_json("roles", {"guoweim": "admin"})
- Agent sessions stored as JSON: storage.put_json("sessions", {...})
- No SQLAlchemy, no models.py, no schemas.py, no crud.py
- List comprehensions replace SQL queries
- Auto-seed on first startup if storage is empty

## Step 3: Replace Custom Auth with canopy_auth

- Remove: login/register pages, JWT tokens, password hashing, forgot/reset password
- Add: from canopy_auth import get_current_user
- User identity from Midway headers (automatic)
- Admin check: user alias in roles dict or DEFAULT_ADMINS list
- DEFAULT_ADMINS = ["guoweim"]

## Step 4: Replace CDN Frontend with Jinja2 Templates

- Remove: React, Ant Design, Babel, dayjs CDN links
- Build: Flask/FastAPI + Jinja2 server-rendered HTML
- Inline CSS (dark sci-fi theme — port existing CSS variables)
- Vanilla JavaScript for: modals, filters, tabs, chart rendering
- No external dependencies — all CSS/JS inline or bundled
- Pages: base layout, browse cards, dashboard, leaderboard, agent chat
- Forms: HTML forms posting to API endpoints
- Modals: vanilla JS show/hide with dark-themed styling

## Step 5: Upgrade AI Agent to Bedrock (canopy_llm)

Current → Canopy:
- Keyword matching → canopy_llm.generate() with case library context in prompt
- Rule-based follow-up → canopy_llm.chat() multi-turn conversation
- Rule-based AI analysis → canopy_llm.generate() with structured analysis prompt
- Hardcoded steps → LLM-generated implementation steps

## Step 6: Port All API Endpoints

All endpoints kept, data layer changes from SQLite to canopy_storage:
- GET /health — keep as-is
- GET/POST/PUT/DELETE /cases — read/write canopy_storage JSON
- GET /cases/options — same (constants.py)
- GET /cases/export — same CSV logic on JSON data
- GET /analytics/* — same aggregation on JSON lists
- GET /rankings — same scoring algorithm
- POST /rankings/{id}/ai-analysis — upgrade to canopy_llm
- POST /agent/design — upgrade to canopy_llm
- POST /agent/followup — upgrade to canopy_llm
- GET /admin/users — read roles from canopy_storage
- PUT/DELETE /admin/users — update roles in canopy_storage

## Step 7: Configuration

```python
PORT = 8080                    # Canopy requirement
HOST = "0.0.0.0"               # Canopy requirement
DEFAULT_ADMINS = ["guoweim"]   # Bootstrap admin
```

## Step 8: Requirements.txt

```
fastapi==0.115.0
uvicorn==0.30.6
jinja2==3.1.4
python-multipart==0.0.9
boto3>=1.34.0
pydantic==2.9.2
```

Removed: sqlalchemy, passlib, python-jose, bcrypt

## Step 9: Local Testing

```bash
set CANOPY_DEV_USER=guoweim
py app.py
# Opens on http://localhost:8080
```

canopy_storage falls back to local filesystem (.canopy_data/) when not on Canopy.

## Step 10: Deploy to Canopy

```powershell
Compress-Archive -Path app.py, requirements.txt, constants.py, ranking.py, analytics.py, agent.py, seed_data.py, templates -DestinationPath canopy-deploy.zip
```

Upload ZIP to https://canopy.fgbs.amazon.dev

---

## Estimated Effort

| Step | Time |
|---|---|
| 1. Restructure | 15 min |
| 2. canopy_storage data layer | 30 min |
| 3. canopy_auth | 15 min |
| 4. Jinja2 templates (biggest) | 2-3 hours |
| 5. Bedrock AI upgrade | 30 min |
| 6. Port endpoints | 30 min |
| 7-10. Config, test, deploy | 15 min |
| **Total** | **~4-5 hours** |

---

## What Gets Better

- AI Agent: real Bedrock Claude instead of keyword matching
- AI Analysis: real LLM insights instead of rule-based
- Auth: seamless Midway SSO, no login page needed
- Access: any Amazon employee globally via URL
- Storage: persistent S3-backed, survives restarts
- Deployment: zip and upload, no EC2/server management

## What Stays the Same

- All 6 phases of functionality
- Dark sci-fi theme
- Card-based browse view with filters
- Dashboard with charts and data table
- Leaderboard with weight sliders (admin only)
- User management (admin only)
- CSV export
- Detail view modal
