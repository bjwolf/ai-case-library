# Canopy Deployment Prompt — IDE System Instruction

> **Version:** 1.1 | **Last Updated:** March 2026
>
> **Purpose:** Paste this entire prompt into your IDE AI assistant (Cline, Amazon Q, Cursor, etc.) as a system instruction / custom workflow. It contains every requirement needed to build apps that deploy **100% successfully** to **Canopy** on the first attempt — including connecting to LLM (Bedrock), persistent storage, and ingesting user identity (Midway).
>
> **How to Use:** Copy → paste into your IDE as a system/project instruction → start building. The AI will follow every constraint automatically.

---

## QUICK REFERENCE CARD

```
CANOPY DEPLOYMENT ESSENTIALS v1.0
================================

HEALTH CHECK  GET /health -> 200 {"status": "healthy"}
PORT          8080 (bind to 0.0.0.0, NOT localhost)
APP OBJECT    Must be named "app" (Flask/FastAPI/Dash)
ENTRY POINT   app.py (Python) | index.js / server.js (Node.js)
DEPENDENCIES  requirements.txt (Python) | package.json (Node.js)
ZIP ROOT      Files at root level, NOT nested in a subfolder
NO DOCKERFILE Platform generates one automatically

RUNTIMES      Python 3.11  |  Node.js 20
COMPUTE       0.25 vCPU / 512 MB  (up to 1 vCPU / 2 GB)
STORAGE       Ephemeral 20 GB + canopy_storage (S3 persistent)

SDK (auto-injected on deploy — do NOT bundle these files):
  canopy_storage.py    -> persistent data (S3-backed key/value)
  canopy_llm.py        -> AI / LLM (Amazon Bedrock, Claude models)
  canopy_auth.py       -> user identity (Midway alias via headers)
  canopy_email.py      -> send emails via SES with templates
  canopy_scheduler.py  -> background jobs (cron & intervals)
  canopy_cache.py      -> in-memory caching with TTL
  canopy_http.py       -> HTTP client with retry & backoff
  canopy_events.py     -> event bus & pre-built triggers

BANNED   External CDNs | SQL databases | OpenAI/GPT | eval()/exec()
```

---

## MISSION

You are building a web application that will deploy to **Canopy** — Amazon internal deployment platform running containers on **ECS Fargate** behind an ALB with Midway authentication. Your goal is to ensure the application follows ALL Canopy requirements so it deploys successfully on the first attempt.

**Core Principles:**
1. **Always add /health first** — number 1 cause of deployment failures
2. **Port 8080, bind 0.0.0.0** — Container networking requires this
3. **Pin all dependency versions** — Reproducible builds
4. **No external CDN links** — Blocked by Content Security Policy
5. **No SQL databases** — Use canopy_storage (S3-backed) or in-memory
6. **No external AI APIs** — Use canopy_llm (Amazon Bedrock)
7. **Relative URLs in JavaScript** — Apps served under /apps/{slug}/
8. **Server-rendered only** — No client-only SPAs without a backend server
9. **Do NOT bundle SDK files** — canopy_*.py (storage, llm, auth, email, scheduler, cache, http, events) are auto-injected

---

# UNIVERSAL REQUIREMENTS (ALL FRAMEWORKS)

## Health Check Endpoint (CRITICAL)

**Every Canopy app MUST expose GET /health returning HTTP 200.**

```python
# Flask
@app.route("/health")
def health():
    return {"status": "healthy"}, 200

# FastAPI
@app.get("/health")
def health():
    return {"status": "healthy"}
```

```javascript
// Express
app.get("/health", (req, res) => res.json({ status: "healthy" }));
```

- Streamlit and Gradio have built-in health checks — no manual endpoint needed
- All other frameworks MUST implement this explicitly
- The platform checks this endpoint every 30 seconds; 3 consecutive failures = restart

## Port and Host (CRITICAL)

- **Port:** 8080 (use process.env.PORT || 8080 for Node.js)
- **Host:** 0.0.0.0 (NOT localhost, NOT 127.0.0.1)

```python
# Python
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

```javascript
// Node.js
app.listen(process.env.PORT || 8080, "0.0.0.0", () => {
  console.log("Server running on port 8080");
});
```

## App Object Naming (CRITICAL)

- Flask/FastAPI/Dash app object MUST be named `app` (or `application` or `server`)
- WRONG: `flask_app = Flask(__name__)` — platform cannot find it
- CORRECT: `app = Flask(__name__)`
- The platform uses importlib.import_module() and looks for the `app` attribute

## if __name__ Guard (CRITICAL)

- ALWAYS wrap app.run() in `if __name__ == "__main__":`
- Flask runs via gunicorn, FastAPI via uvicorn in production
- Without the guard, app.run() conflicts with the production server

## CORS Middleware (CRITICAL)

Required for the preview iframe and cross-origin requests:

```python
# Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
```

```python
# FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

## Relative URLs in JavaScript (CRITICAL)

Apps are served behind a reverse proxy under /apps/{slug}/:
- CORRECT: fetch("api/data") — relative to page base URL
- WRONG: fetch("/api/data") — resolves to platform root, returns 404
- Same for form action, a href, link href in HTML templates
- Python/Node route decorators (@app.route("/api/...")) are fine — prefix stripping is handled server-side

## Dependencies File (CRITICAL)

- **Python:** requirements.txt with pinned versions at ZIP root
  Example:
  flask==3.0.0
  flask-cors==4.0.0
  boto3>=1.34.0
  pandas==2.1.0

- **Node.js:** package.json with dependencies and start script at ZIP root

## No Dockerfile

The platform auto-generates a Dockerfile based on framework detection. Do NOT include one.

## Server-Rendered Only

- NO client-only SPAs (create-react-app, Vite, Vue CLI, Angular CLI without a backend)
- YES: Flask + Jinja2 templates, Express + EJS, Streamlit, Dash
- If you need a React/Vue frontend, serve it from an Express or Flask server

## Environment Variables

Never hardcode secrets. Use os.environ.get() or process.env for configuration.

---

# SECURITY REQUIREMENTS

## External CDN Ban (Content Security Policy)

ALL external CDN links are BLOCKED. Apps using them render as blank white pages.

BANNED:
- Font Awesome, Bootstrap, Tailwind, Google Fonts from any CDN
- ANY external stylesheet or script tag pointing to third-party domains

USE INSTEAD:
- Inline SVG icons instead of Font Awesome
- Inline style blocks with CSS instead of Bootstrap/Tailwind CDN
- System font stack: font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif;
- Install CSS frameworks as npm/pip packages and serve locally

## External AI API Ban

- NO OpenAI, Google AI (Gemini), Anthropic direct API, Cohere, Hugging Face Inference, Replicate
- USE canopy_llm (Amazon Bedrock) — auto-injected, zero config

## Code Security Rules

- NEVER eval() or exec() — use json.loads(), ast.literal_eval()
- NEVER os.system() — use subprocess.run(shell=False)
- NEVER pickle.loads() on untrusted data
- NEVER hardcode passwords, API keys, or secrets
- NEVER subprocess with shell=True

---

# COMPUTE AND INFRASTRUCTURE

| Resource | Default | Maximum |
|----------|---------|---------|
| CPU | 0.25 vCPU | 1 vCPU |
| Memory | 512 MB | 2 GB |
| Ephemeral Storage | 20 GB | 20 GB |
| Startup Grace Period | 120 seconds | — |
| Health Check Interval | 30 seconds | — |

Ephemeral storage is lost on container restart. For persistent data, use canopy_storage.

---

# BANNED DEPENDENCIES

## Python — Too Large or Unavailable
```
tensorflow, torch, pytorch, transformers     # Too large for 512 MB
opencv-python, cv2                           # Requires system libs not in image
psycopg2, mysqlclient, pymongo, redis        # No database available
celery                                        # No message broker
scipy, scikit-learn, xgboost, lightgbm       # May exceed memory
dask, pyspark                                 # No distributed computing
docker                                        # No Docker-in-Docker
openai, anthropic, google-generativeai        # External AI banned
cohere, huggingface_hub, replicate            # External AI banned
```

## Node.js — Too Large or Unavailable
```
@tensorflow/tfjs-node    # Too large
puppeteer, playwright    # Requires browsers
sharp, canvas            # Requires native compilation
pg, mysql2, mongodb      # No database
redis, bull              # No Redis
openai                   # External AI banned
```

## Safe Dependencies (OK to use)
```
pandas (~80 MB), numpy (~30 MB), matplotlib (~50 MB), plotly (~30 MB)
seaborn (~10 MB), pillow (~10 MB), openpyxl (~5 MB), boto3 (~30 MB)
httpx (~5 MB), requests (~5 MB), beautifulsoup4 (~1 MB), pydantic (~5 MB)
jinja2, markupsafe, python-dateutil, pytz, chardet
```

---

# AI / LLM — canopy_llm (Amazon Bedrock)

## Overview

canopy_llm.py is **auto-injected** into every deployed app. It wraps Amazon Bedrock with Claude models, automatic model rotation, and throttle handling. You do NOT need to include this file in your ZIP — just import it.

## Setup

1. Add boto3>=1.34.0 for storage/llm/email.
2. Import and use:

```python
from canopy_llm import CanopyLLM

llm = CanopyLLM(system_prompt="You are a helpful assistant.")

# Single-shot generation
response = llm.generate("Summarize this text...")

# Multi-turn chat
response = llm.chat([
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What can you do?"}
])

# Convenience methods
summary = llm.summarize(long_text, style="bullet_points")
label = llm.classify(text, categories=["positive", "negative", "neutral"])
data = llm.extract(text, fields=["name", "date", "amount"])

# Streaming
for chunk in llm.stream("Write a story about..."):
    print(chunk, end="")
```

## Available Methods

| Method | Purpose |
|--------|---------|
| generate(prompt) | Single-shot text generation |
| chat(messages) | Multi-turn conversation |
| summarize(text, style) | Summarize text (paragraph, bullet_points, tldr) |
| classify(text, categories) | Classify text into categories |
| extract(text, fields) | Extract structured data from text |
| stream(prompt) | Stream tokens as they are generated |

## Node.js

For Node.js apps, use @aws-sdk/client-bedrock-runtime directly:
```javascript
const { BedrockRuntimeClient, InvokeModelCommand } = require("@aws-sdk/client-bedrock-runtime");
const client = new BedrockRuntimeClient({ region: process.env.AWS_REGION || "us-east-1" });
```

---

# canopy_storage — Persistent Data (S3-Backed)

## Overview

canopy_storage.py is **auto-injected** into every deployed app. It provides persistent key-value storage backed by S3, automatically partitioned per app. You do NOT need to include this file in your ZIP — just import it.

## Setup

1. Add boto3>=1.34.0 for storage/llm/email.
2. Import and use:

```python
from canopy_storage import CanopyStorage

storage = CanopyStorage()  # auto-configured from environment

# Write
storage.put("notes.txt", "Hello world")
storage.put_json("todos", [{"id": 1, "text": "Buy groceries", "done": False}])
storage.put_bytes("model.pkl", model_bytes)
storage.put_file("report.pdf", "/tmp/report.pdf")

# Read
text = storage.get("notes.txt")
todos = storage.get_json("todos")          # auto-parses JSON
raw = storage.get_bytes("model.pkl")
storage.download_file("report.pdf", "/tmp/report.pdf")

# Query
keys = storage.list_keys()                 # list all keys
keys = storage.list_keys(prefix="reports/") # filter by prefix
exists = storage.exists("notes.txt")

# Delete
storage.delete("old-file.txt")
storage.delete_all(prefix="temp/")         # bulk delete

# Convenience
data = storage.get_or_default("settings", {"theme": "light"})
storage.append_to_list("log", {"event": "login", "user": "jdoe"})
```

## Full API

| Method | Purpose |
|--------|---------|
| put(key, text) | Store text |
| put_json(key, data) | Store JSON (auto-appends .json) |
| put_bytes(key, bytes) | Store binary data |
| put_file(key, filepath) | Upload a local file |
| get(key) | Read text (None if missing) |
| get_json(key) | Read and parse JSON |
| get_bytes(key) | Read raw bytes |
| download_file(key, path) | Download to local file |
| list_keys(prefix) | List stored keys |
| exists(key) | Check if key exists |
| delete(key) | Delete one key |
| delete_all(prefix) | Delete all keys under prefix |
| get_or_default(key, default) | Get JSON with fallback |
| append_to_list(key, item) | Append to a JSON list |

## Local Development

When APP_DATA_BUCKET is not set, CanopyStorage automatically falls back to local filesystem at .canopy_data/{owner}/{slug}/:

```python
storage = CanopyStorage(owner="myalias", slug="my-app")
storage.put_json("test", {"hello": "world"})
# Saved to .canopy_data/myalias/my-app/test.json
```

---

# canopy_auth — User Identity (Midway)

## Overview

canopy_auth.py is **auto-injected** into every deployed app. It reads the authenticated visitor Amazon alias from auth-proxy headers injected by Canopy Midway integration. You do NOT need to include this file in your ZIP — just import it.

## How It Works

1. Visitor hits your app URL
2. ALB + Cognito authenticates via Midway
3. Auth-proxy sidecar extracts the alias from OIDC JWT tokens
4. Your app reads the alias via canopy_auth

## Usage

```python
from canopy_auth import get_current_user, require_auth

# Flask
@app.route("/dashboard")
def dashboard():
    user = get_current_user()  # Returns "jdoe" or None
    return f"Hello, {user}!"

# FastAPI
@app.get("/api/data")
def get_data(request: Request):
    user = get_current_user(request)
    return {"user": user}

# Streamlit (auto-detects st.context.headers)
user = get_current_user()
st.write(f"Welcome, {user}!")

# Require auth (raises ValueError if not authenticated)
user = require_auth()
```

## Node.js

```javascript
// Read the auth header directly
app.get("/api/data", (req, res) => {
  const user = req.headers["x-canopy-user"] || req.headers["x-amzn-oidc-identity"] || "anonymous";
  res.json({ user, data: [] });
});
```

## Local Development

```bash
export CANOPY_DEV_USER=myalias
python app.py
```

Or: get_current_user(default_user="myalias")

## SDK Summary

| Helper | Purpose | requirements.txt | Auto-Injected |
|--------|---------|-----------------|---------------|
| canopy_storage | Persistent data (S3) | boto3>=1.34.0 | Yes |
| canopy_llm | AI / LLM (Bedrock) | boto3>=1.34.0 | Yes |
| canopy_auth | User identity (Midway) | None | Yes |
| canopy_email | Send emails via SES | boto3>=1.34.0 | Yes |
| canopy_scheduler | Background jobs (cron/intervals) | None | Yes |
| canopy_cache | In-memory caching with TTL | None | Yes |
| canopy_http | HTTP client with retry/backoff | None | Yes |
| canopy_events | Event bus & pre-built triggers | None | Yes |

For local development, download the SDK files:
curl -O https://canopy.fgbs.amazon.dev/api/v1/files/sdk/canopy_storage.py
curl -O https://canopy.fgbs.amazon.dev/api/v1/files/sdk/canopy_llm.py
curl -O https://canopy.fgbs.amazon.dev/api/v1/files/sdk/canopy_auth.py

---

# DATA PERSISTENCE PATTERNS

## NO SQL Databases

SQLite, PostgreSQL, MySQL, MongoDB, Redis, DynamoDB direct — ALL unavailable.

## Choose Based on Need

### Pattern 1: No Persistence (Upload, Process, Download)
```python
uploaded_file = request.files["file"]
df = pd.read_csv(uploaded_file)
result = process(df)
return send_file(io.BytesIO(result.to_csv().encode()), as_attachment=True)
```

### Pattern 2: Ephemeral In-Memory (Lost on Restart)
```python
DATA_STORE = {}

@app.route("/api/items", methods=["POST"])
def add_item():
    item = request.get_json()
    DATA_STORE[item["id"]] = item
    return jsonify(item), 201
```

### Pattern 3: Persistent via canopy_storage (Recommended)
```python
from canopy_storage import CanopyStorage
storage = CanopyStorage()
storage.put_json("todos", [{"id": 1, "text": "Buy groceries", "done": False}])
todos = storage.get_or_default("todos", [])
```

---

# PYTHON FRAMEWORKS

| Framework | Entry File | Health Check | CORS |
|-----------|------------|--------------|------|
| Streamlit | app.py | Built-in | N/A |
| Flask | app.py | @app.route("/health") | flask-cors required |
| FastAPI | app.py | @app.get("/health") | CORSMiddleware required |
| Dash | app.py | @server.route("/health") | Inherits from Flask |
| Django | manage.py | Custom view | django-cors-headers |
| Gradio | app.py | Built-in | N/A |

## Python Project Structure
```
my-python-app/
  app.py              # Main entry point (REQUIRED)
  requirements.txt    # Dependencies with pinned versions (REQUIRED)
  templates/          # HTML templates (Flask/Django)
  static/             # Static assets
  README.md
```
(canopy_*.py SDK files are auto-injected — do NOT include them)

## Python Entry Point Priority
1. app.py (preferred)
2. main.py
3. server.py
4. application.py
5. run.py
6. wsgi.py
7. index.py
8. manage.py (Django)

## Flask Resource Path Resolution (CRITICAL)
```python
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))
```

---

# NODE.JS FRAMEWORKS

| Framework | Entry File | Start Command | Health Check |
|-----------|------------|---------------|--------------|
| Express | index.js | node index.js | app.get("/health", ...) |
| NestJS | src/main.ts | node dist/main.js | Via adapter |
| Koa | app.js | node app.js | router.get("/health", ...) |
| Fastify | server.js | node server.js | fastify.get("/health", ...) |
| Hapi | server.js | node server.js | server.route({ path: "/health" }) |

## Node.js Entry Point Priority
1. npm start (if defined in package.json)
2. dist/main.js
3. dist/index.js
4. build/index.js
5. index.js
6. server.js
7. app.js
8. src/index.js

---

# COMPLETE FLASK EXAMPLE (with all Canopy SDK connectors)

```python
"""
My Canopy App — Flask example with storage, LLM, and auth.
All canopy_* SDK files (storage, llm, auth, email, scheduler, cache, http, events) are
auto-injected by Canopy on deploy. Just import them.
"""
import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# SDK imports — these files are auto-injected on deploy
from canopy_storage import CanopyStorage
from canopy_llm import CanopyLLM
from canopy_auth import get_current_user

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)  # MUST be named "app"
CORS(app)

storage = CanopyStorage()
llm = CanopyLLM(system_prompt="You are a helpful assistant.")


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


@app.route("/")
def index():
    user = get_current_user()
    return render_template_string(
        "<h1>Hello {{ user }}!</h1>"
        "<p>Your notes: {{ notes }}</p>"
        "<form method=post action=api/note>"
        "<input name=note><button>Save</button>"
        "</form>",
        user=user or "anonymous",
        notes=storage.get_or_default("notes", []),
    )


@app.route("/api/note", methods=["POST"])
def save_note():
    user = get_current_user()
    note = request.form.get("note", "")
    storage.append_to_list("notes", {"user": user, "note": note})
    return jsonify({"ok": True})


@app.route("/api/ask", methods=["POST"])
def ask_ai():
    data = request.get_json()
    response = llm.generate(data.get("question", "Hello"))
    return jsonify({"answer": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
```

requirements.txt:
```
flask==3.0.0
flask-cors==4.0.0
boto3>=1.34.0
```

---

# ZIP FILE STRUCTURE (CRITICAL)

Files MUST be at ZIP root: my-app.zip contains app.py, requirements.txt
NOT nested: my-app.zip containing my-app/app.py is WRONG

Exclude: venv/, node_modules/, __pycache__/, .git/, dist/, .env

---

# DEPLOYMENT CHECKLIST

- [ ] /health endpoint returns 200 {"status": "healthy"}
- [ ] App listens on port 8080, binds to 0.0.0.0
- [ ] App object named "app" (Flask/FastAPI)
- [ ] app.run() inside if __name__ == "__main__": guard
- [ ] CORS middleware enabled
- [ ] requirements.txt OR package.json at ZIP root
- [ ] No node_modules/ or venv/ in ZIP
- [ ] Files at ZIP root (not nested)
- [ ] No hardcoded secrets
- [ ] No external CDN links
- [ ] No banned dependencies
- [ ] JavaScript uses relative URLs (no leading /)
- [ ] boto3>=1.34.0 if using canopy_llm or canopy_storage
- [ ] ZIP under 500 MB
- [ ] SDK files NOT bundled (they are auto-injected)

---

# TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Health check failed | Add /health endpoint returning {"status": "healthy"} |
| Connection refused | Use port 8080, bind to 0.0.0.0 |
| Blank white page | Remove external CDN links (blocked by CSP) |
| 404 on API calls | Use relative URLs: fetch("api/data") not fetch("/api/data") |
| CORS error | Add flask-cors or CORSMiddleware |
| Module not found | Name app object "app", not "flask_app" |
| Port conflict | Wrap app.run() in if __name__ == "__main__": |
| Templates not found | Use os.path-based template_folder in Flask |
| canopy_storage error | Add boto3>=1.34.0 for storage/llm/email.|
| Auth returns None | Check x-canopy-user header; locally set CANOPY_DEV_USER |

---

- Wiki: DaS-FinTech/Products/Canopy (https://w.amazon.com/bin/view/DaS-FinTech/Products/Canopy/)
- Slack: #canopy-platform-interest

**Version:** 1.1 (Mar 2026) — Full SDK coverage: storage, llm, auth, email, scheduler, cache, http, events