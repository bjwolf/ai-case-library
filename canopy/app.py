"""GSRC AI Initiatives Repository — Canopy Version"""
import os
import uuid
import csv
import io
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

# Canopy SDK — auto-injected on deploy, local fallback for dev
try:
    from canopy_storage import CanopyStorage
except ImportError:
    CanopyStorage = None
try:
    from canopy_llm import CanopyLLM
except ImportError:
    CanopyLLM = None
try:
    from canopy_auth import get_current_user as canopy_get_user
except ImportError:
    canopy_get_user = None

from constants import *
from seed_data import SAMPLE_CASES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

DEFAULT_ADMINS = ["guoweim"]

# --- Storage ---
class DataStore:
    """Wraps canopy_storage or falls back to in-memory + local JSON."""
    def __init__(self):
        self.storage = CanopyStorage() if CanopyStorage else None
        self._mem = {}

    def get_json(self, key, default=None):
        if self.storage:
            return self.storage.get_or_default(key, default or [])
        if key not in self._mem:
            self._mem[key] = default if default is not None else []
        return self._mem[key]

    def put_json(self, key, data):
        if self.storage:
            self.storage.put_json(key, data)
        self._mem[key] = data

store = DataStore()

def seed_if_empty():
    cases = store.get_json("cases", [])
    if not cases:
        for c in SAMPLE_CASES:
            c["id"] = str(uuid.uuid4())
            c["date_created"] = datetime.utcnow().isoformat()
            c["date_updated"] = datetime.utcnow().isoformat()
        store.put_json("cases", SAMPLE_CASES)
        store.put_json("roles", {a: "admin" for a in DEFAULT_ADMINS})
        print(f"Seeded {len(SAMPLE_CASES)} cases and {len(DEFAULT_ADMINS)} admin(s)")

seed_if_empty()

# --- LLM ---
llm = None
if CanopyLLM:
    llm = CanopyLLM(system_prompt="You are an AI solution design expert. You help teams design AI automation solutions based on a library of existing AI initiatives.")

# --- Auth helper ---
def get_user(request: Request) -> str:
    if canopy_get_user:
        try:
            return canopy_get_user(request) or "anonymous"
        except:
            pass
    return os.environ.get("CANOPY_DEV_USER", "anonymous")

def get_role(user: str) -> str:
    roles = store.get_json("roles", {})
    if user in DEFAULT_ADMINS and user not in roles:
        roles[user] = "admin"
        store.put_json("roles", roles)
    elif user not in roles:
        roles[user] = "learner"
        store.put_json("roles", roles)
    return roles.get(user, "learner")

def is_admin(user: str) -> bool:
    return get_role(user) == "admin"

# --- Health ---
@app.get("/health")
def health():
    return {"status": "healthy", "llm_available": llm is not None}

# --- Pages ---
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = get_user(request)
    cases = store.get_json("cases", [])
    return templates.TemplateResponse("browse.html", {
        "request": request, "user": user, "role": get_role(user),
        "cases": cases, "options": get_all_options(), "tab": "browse",
    })

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    user = get_user(request)
    cases = store.get_json("cases", [])
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "role": get_role(user),
        "cases": cases, "options": get_all_options(), "tab": "dashboard",
    })

@app.get("/mine", response_class=HTMLResponse)
def mine_page(request: Request):
    user = get_user(request)
    cases = [c for c in store.get_json("cases", []) if c.get("owner_login") == user]
    return templates.TemplateResponse("browse.html", {
        "request": request, "user": user, "role": get_role(user),
        "cases": cases, "options": get_all_options(), "tab": "mine",
    })

@app.get("/leaderboard", response_class=HTMLResponse)
def leaderboard_page(request: Request):
    user = get_user(request)
    if not is_admin(user):
        raise HTTPException(403, "Admin only")
    return templates.TemplateResponse("leaderboard.html", {
        "request": request, "user": user, "role": get_role(user), "tab": "leaderboard",
    })

@app.get("/agent", response_class=HTMLResponse)
def agent_page(request: Request):
    user = get_user(request)
    return templates.TemplateResponse("agent.html", {
        "request": request, "user": user, "role": get_role(user), "tab": "agent",
    })

# --- API: Options ---
def get_all_options():
    return {"job_levels": JOB_LEVELS, "programs_teams": PROGRAMS_TEAMS,
            "ai_techniques": AI_TECHNIQUES, "statuses": STATUSES,
            "platforms": PLATFORMS, "dev_types": DEV_TYPES, "is_chatbot": IS_CHATBOT}

@app.get("/api/options")
def api_options():
    return get_all_options()

# --- API: Cases CRUD ---
@app.get("/api/cases")
def api_list_cases(search: Optional[str] = None):
    cases = store.get_json("cases", [])
    if search:
        t = search.lower()
        cases = [c for c in cases if t in (c.get("use_case_title","")).lower()
                 or t in (c.get("owner_login","")).lower()
                 or t in (c.get("program_team","")).lower()
                 or t in (c.get("ai_technique","")).lower()
                 or t in (c.get("problem_statement","")).lower()]
    return cases

@app.get("/api/cases/{case_id}")
def api_get_case(case_id: str):
    cases = store.get_json("cases", [])
    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        raise HTTPException(404, "Not found")
    return case

@app.post("/api/cases")
async def api_create_case(request: Request):
    user = get_user(request)
    data = await request.json()
    data["id"] = str(uuid.uuid4())
    data["owner_login"] = user
    data["date_created"] = datetime.utcnow().isoformat()
    data["date_updated"] = datetime.utcnow().isoformat()
    # Convert numeric strings
    for f in ["time_saved","yearly_hc_saved","accuracy","cost_reduction","yearly_usd_saved","dev_time_hours","scalability_score","innovation_score"]:
        if f in data and data[f] not in (None, ""):
            try: data[f] = float(data[f])
            except: pass
        elif f in data and data[f] == "":
            data[f] = None
    cases = store.get_json("cases", [])
    cases.append(data)
    store.put_json("cases", cases)
    return data

@app.put("/api/cases/{case_id}")
async def api_update_case(case_id: str, request: Request):
    user = get_user(request)
    data = await request.json()
    cases = store.get_json("cases", [])
    idx = next((i for i, c in enumerate(cases) if c["id"] == case_id), None)
    if idx is None:
        raise HTTPException(404, "Not found")
    if not is_admin(user) and cases[idx].get("owner_login") != user:
        raise HTTPException(403, "Not your case")
    for f in ["time_saved","yearly_hc_saved","accuracy","cost_reduction","yearly_usd_saved","dev_time_hours","scalability_score","innovation_score"]:
        if f in data and data[f] not in (None, ""):
            try: data[f] = float(data[f])
            except: pass
        elif f in data and data[f] == "":
            data[f] = None
    data["date_updated"] = datetime.utcnow().isoformat()
    cases[idx].update({k: v for k, v in data.items() if v is not None or k in data})
    store.put_json("cases", cases)
    return cases[idx]

@app.delete("/api/cases/{case_id}")
def api_delete_case(case_id: str, request: Request):
    user = get_user(request)
    cases = store.get_json("cases", [])
    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        raise HTTPException(404, "Not found")
    if not is_admin(user) and case.get("owner_login") != user:
        raise HTTPException(403, "Not your case")
    cases = [c for c in cases if c["id"] != case_id]
    store.put_json("cases", cases)
    return {"detail": "Deleted"}

# --- API: CSV Export ---
@app.get("/api/cases/export")
def api_export():
    cases = store.get_json("cases", [])
    out = io.StringIO()
    w = csv.writer(out)
    headers = ["ID","Owner","Program","Title","AI Technique","Platform","Dev Type","Chatbot","Status",
               "Time%","HC/yr","Acc%","Cost%","USD/yr","Dev Hrs","Scalability","Innovation"]
    w.writerow(headers)
    for c in cases:
        w.writerow([c.get("id"),c.get("owner_login"),c.get("program_team"),c.get("use_case_title"),
            c.get("ai_technique"),c.get("platform"),c.get("dev_type"),c.get("is_chatbot"),c.get("status"),
            c.get("time_saved"),c.get("yearly_hc_saved"),c.get("accuracy"),c.get("cost_reduction"),
            c.get("yearly_usd_saved"),c.get("dev_time_hours"),c.get("scalability_score"),c.get("innovation_score")])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ai_initiatives.csv"})

# --- API: Analytics ---
@app.get("/api/analytics/summary")
def api_summary():
    cases = store.get_json("cases", [])
    n = len(cases)
    def avg(field): vals = [c.get(field) for c in cases if c.get(field) is not None]; return round(sum(vals)/len(vals),1) if vals else 0
    def total(field): return round(sum(c.get(field,0) or 0 for c in cases),1)
    return {"total": n, "avg_time_saved": avg("time_saved"), "total_hc_saved": total("yearly_hc_saved"),
            "total_usd_saved": total("yearly_usd_saved"), "total_dev_hours": total("dev_time_hours"), "avg_accuracy": avg("accuracy")}

@app.get("/api/analytics/by-program")
def api_by_program():
    cases = store.get_json("cases", [])
    groups = {}
    for c in cases:
        p = c.get("program_team","Unknown")
        if p not in groups: groups[p] = {"program":p,"count":0,"total_usd_saved":0}
        groups[p]["count"] += 1
        groups[p]["total_usd_saved"] += c.get("yearly_usd_saved",0) or 0
    return list(groups.values())

@app.get("/api/analytics/by-technique")
def api_by_technique():
    cases = store.get_json("cases", [])
    counts = {}
    for c in cases:
        t = c.get("ai_technique","Unknown")
        counts[t] = counts.get(t,0) + 1
    return [{"technique":k,"count":v} for k,v in counts.items()]

@app.get("/api/analytics/by-status")
def api_by_status():
    cases = store.get_json("cases", [])
    counts = {}
    for c in cases:
        s = c.get("status","Unknown")
        counts[s] = counts.get(s,0) + 1
    return [{"status":k,"count":v} for k,v in counts.items()]

@app.get("/api/analytics/by-platform")
def api_by_platform():
    cases = store.get_json("cases", [])
    counts = {}
    for c in cases:
        p = c.get("platform")
        if p: counts[p] = counts.get(p,0) + 1
    return [{"platform":k,"count":v} for k,v in counts.items()]

@app.get("/api/analytics/by-dev-type")
def api_by_dev_type():
    cases = store.get_json("cases", [])
    counts = {}
    for c in cases:
        d = c.get("dev_type")
        if d: counts[d] = counts.get(d,0) + 1
    return [{"dev_type":k,"count":v} for k,v in counts.items()]

@app.get("/api/analytics/by-chatbot")
def api_by_chatbot():
    cases = store.get_json("cases", [])
    counts = {}
    for c in cases:
        cb = c.get("is_chatbot")
        if cb: counts[cb] = counts.get(cb,0) + 1
    return [{"is_chatbot":k,"count":v} for k,v in counts.items()]

@app.get("/api/analytics/trends")
def api_trends():
    cases = store.get_json("cases", [])
    months = {}
    for c in cases:
        d = c.get("date_created","")[:7]
        if d: months[d] = months.get(d,0) + 1
    return [{"month":k,"count":v} for k,v in sorted(months.items())]

# --- API: Rankings ---
@app.get("/api/rankings")
def api_rankings(impact_w:int=40, scalability_w:int=25, effort_w:int=20, innovation_w:int=15):
    from ranking import compute_rankings
    cases = store.get_json("cases", [])
    return compute_rankings(cases, impact_w, scalability_w, effort_w, innovation_w)

@app.post("/api/rankings/{case_id}/ai-analysis")
async def api_ai_analysis(case_id: str):
    from ranking import compute_rankings, generate_analysis
    cases = store.get_json("cases", [])
    rankings = compute_rankings(cases)
    case_data = next((r for r in rankings if r["id"] == case_id), None)
    if not case_data:
        raise HTTPException(404, "Not found")
    summary = {"avg_time_saved": 0, "avg_cost_reduction": 0, "avg_accuracy": 0}
    vals = lambda f: [c.get(f) for c in cases if c.get(f) is not None]
    for f in ["time_saved","cost_reduction","accuracy"]:
        v = vals(f)
        summary[f"avg_{f}"] = round(sum(v)/len(v),1) if v else 0
    if llm:
        prompt = f"Analyze this AI initiative:\n{case_data}\n\nLibrary averages: {summary}\n\nProvide JSON with keys: strengths (list), weaknesses (list), suggestions (list), risks (list), summary (string)."
        try:
            resp = llm.generate(prompt)
            import json
            return json.loads(resp)
        except:
            pass
    return generate_analysis(case_data, summary, rankings)

# --- API: Agent ---
_sessions = {}

@app.post("/api/agent/design")
async def api_agent_design(request: Request):
    from agent import handle_design
    data = await request.json()
    query = data.get("query","")
    if not query.strip():
        raise HTTPException(400, "Query required")
    cases = store.get_json("cases", [])
    if llm:
        sid = str(uuid.uuid4())
        case_summary = "\n".join([f"- {c.get('use_case_title')}: {c.get('ai_technique')}, {c.get('problem_statement','')[:100]}" for c in cases[:20]])
        prompt = f"Based on these existing AI initiatives:\n{case_summary}\n\nDesign an AI solution for: {query}\n\nReturn JSON with: recommendation, technique, tools (list), estimated_effort_hours, implementation_steps (list), matched_cases (list of titles)."
        try:
            resp = llm.generate(prompt)
            import json
            design = json.loads(resp)
            _sessions[sid] = {"query": query, "history": [{"role":"user","content":query},{"role":"assistant","content":resp}]}
            return {"session_id": sid, "design": design}
        except:
            pass
    return handle_design(query, cases)

@app.post("/api/agent/followup")
async def api_agent_followup(request: Request):
    from agent import handle_followup_local
    data = await request.json()
    sid = data.get("session_id","")
    question = data.get("question","")
    cases = store.get_json("cases", [])
    if llm and sid in _sessions:
        _sessions[sid]["history"].append({"role":"user","content":question})
        try:
            resp = llm.chat(_sessions[sid]["history"])
            _sessions[sid]["history"].append({"role":"assistant","content":resp})
            return {"session_id": sid, "answer": resp}
        except:
            pass
    return handle_followup_local(sid, question, cases)

# --- API: Admin ---
@app.get("/api/admin/users")
def api_list_users(request: Request):
    user = get_user(request)
    if not is_admin(user):
        raise HTTPException(403, "Admin only")
    roles = store.get_json("roles", {})
    return [{"login": k, "role": v} for k, v in roles.items()]

@app.put("/api/admin/users/{login}/role")
async def api_update_role(login: str, request: Request):
    user = get_user(request)
    if not is_admin(user):
        raise HTTPException(403, "Admin only")
    data = await request.json()
    roles = store.get_json("roles", {})
    roles[login] = data.get("role", "learner")
    store.put_json("roles", roles)
    return {"detail": f"Role updated to {roles[login]}"}

@app.delete("/api/admin/users/{login}")
def api_delete_user(login: str, request: Request):
    user = get_user(request)
    if not is_admin(user):
        raise HTTPException(403, "Admin only")
    if login in DEFAULT_ADMINS:
        raise HTTPException(400, "Cannot delete default admin")
    roles = store.get_json("roles", {})
    roles.pop(login, None)
    store.put_json("roles", roles)
    return {"detail": "Deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
