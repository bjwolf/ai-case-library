# AI Case Library — AI Ascent Hackathon 2026

A full-stack AI initiative management platform with case library, analytics dashboard, ranking engine, and AI solution design agent.

## Quick Start

Prerequisites: Python 3.10+ (check with `py --version`)

```bash
cd backend
py -m pip install -r requirements.txt
py seed_data.py
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ in your browser.

Default admin login: `admin` / `admin123`

## Features

- Submit & manage AI initiatives with full CRUD
- User auth with roles (learner / admin)
- Filterable browse table with search, sort, CSV export
- Analytics dashboard with summary cards and charts
- Weighted ranking leaderboard with AI analysis (admin only)
- AI Solution Design Agent — describe a problem, get a solution design
