from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import csv
import io

from app.database import engine, get_db, Base
from app.schemas import CaseCreate, CaseUpdate, CaseResponse
from app import crud
from app.constants import JOB_LEVELS, PROGRAMS_TEAMS, AI_TECHNIQUES, STATUSES, PLATFORMS, DEV_TYPES, IS_CHATBOT
from app.models import User
from app import analytics as analytics_mod
from app.ranking import get_rankings, generate_ai_analysis
from app.agent import handle_design_query, handle_followup
from app.auth import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    PasswordResetRequest, PasswordResetConfirm,
    hash_password, verify_password, create_access_token,
    get_current_user, require_user, require_admin, send_reset_email,
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Case Library API",
    description="Backend API for the AI Ascent Hackathon Case Library",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---- Auth Endpoints ----
@app.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.login == data.login).first():
        raise HTTPException(400, "Login already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(
        login=data.login, email=data.email, display_name=data.display_name,
        hashed_password=hash_password(data.password), role="learner",
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": user.login, "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

@app.post("/auth/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == data.login).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(401, "Invalid login or password")
    token = create_access_token({"sub": user.login, "role": user.role})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

@app.get("/auth/me", response_model=UserResponse)
def get_me(user: User = Depends(require_user)):
    return user

@app.post("/auth/forgot-password")
def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    import uuid
    from datetime import datetime, timedelta, timezone
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"detail": "If the email exists, a reset link has been sent"}
    token = str(uuid.uuid4())
    user.reset_token = token
    user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()
    send_reset_email(user.email, token)
    return {"detail": "If the email exists, a reset link has been sent"}

@app.post("/auth/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    from datetime import datetime, timezone
    user = db.query(User).filter(User.reset_token == data.token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.now(timezone.utc):
        raise HTTPException(400, "Invalid or expired reset token")
    user.hashed_password = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.commit()
    return {"detail": "Password reset successful"}


@app.get("/admin/users")
def list_users(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    users = db.query(User).all()
    return [{"id": u.id, "login": u.login, "email": u.email, "display_name": u.display_name, "role": u.role, "is_active": u.is_active} for u in users]

@app.put("/admin/users/{user_id}/role")
def update_user_role(user_id: str, body: dict, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    if body.get("role") not in ("learner", "admin"):
        raise HTTPException(400, "Role must be 'learner' or 'admin'")
    target.role = body["role"]
    db.commit()
    return {"detail": f"Role updated to {body['role']}"}

@app.delete("/admin/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    if target.login == "admin":
        raise HTTPException(400, "Cannot delete the default admin")
    db.delete(target)
    db.commit()
    return {"detail": "User deleted"}

@app.post("/admin/users")
def admin_create_user(body: dict, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if db.query(User).filter(User.login == body.get("login")).first():
        raise HTTPException(400, "Login already taken")
    new_user = User(
        login=body["login"], email=body.get("email", ""), display_name=body.get("display_name", body["login"]),
        hashed_password=hash_password(body.get("password", "changeme")), role=body.get("role", "learner"),
    )
    db.add(new_user); db.commit()
    return {"detail": f"User {body['login']} created"}


@app.post("/cases", response_model=CaseResponse, status_code=201)
def create_case(case: CaseCreate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    case.owner_login = user.login
    return crud.create_case(db, case)


@app.get("/cases", response_model=list[CaseResponse])
def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    program_team: Optional[str] = None,
    ai_technique: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "date_created",
    order: str = "desc",
    mine_only: bool = False,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    owner = user.login if (mine_only and user) else None
    return crud.get_cases(db, skip, limit, program_team, ai_technique, status, sort_by, order, owner_login=owner, search=search)


@app.get("/cases/options")
def get_options():
    return {
        "job_levels": JOB_LEVELS,
        "programs_teams": PROGRAMS_TEAMS,
        "ai_techniques": AI_TECHNIQUES,
        "statuses": STATUSES,
        "platforms": PLATFORMS,
        "dev_types": DEV_TYPES,
        "is_chatbot": IS_CHATBOT,
    }


@app.get("/analytics/summary")
def analytics_summary(db: Session = Depends(get_db)):
    return analytics_mod.get_summary(db)


@app.post("/agent/design")
def agent_design(body: dict, db: Session = Depends(get_db)):
    query = body.get("query", "")
    session_id = body.get("session_id")
    if not query.strip():
        raise HTTPException(400, "Query is required")
    return handle_design_query(db, query, session_id)


@app.post("/agent/followup")
def agent_followup(body: dict, db: Session = Depends(get_db)):
    session_id = body.get("session_id")
    question = body.get("question", "")
    if not session_id or not question.strip():
        raise HTTPException(400, "session_id and question are required")
    return handle_followup(db, session_id, question)


@app.get("/rankings")
def rankings(
    impact_w: int = 40, scalability_w: int = 25,
    effort_w: int = 20, innovation_w: int = 15,
    db: Session = Depends(get_db),
):
    return get_rankings(db, impact_w, scalability_w, effort_w, innovation_w)


@app.post("/rankings/{case_id}/ai-analysis")
def ai_analysis(case_id: str, db: Session = Depends(get_db)):
    rankings_data = get_rankings(db)
    case_data = next((r for r in rankings_data if r["id"] == case_id), None)
    if not case_data:
        raise HTTPException(404, "Case not found")
    summary = analytics_mod.get_summary(db)
    return generate_ai_analysis(case_data, summary, rankings_data)

@app.get("/analytics/by-program")
def analytics_by_program(db: Session = Depends(get_db)):
    return analytics_mod.get_by_program(db)

@app.get("/analytics/by-technique")
def analytics_by_technique(db: Session = Depends(get_db)):
    return analytics_mod.get_by_technique(db)

@app.get("/analytics/by-status")
def analytics_by_status(db: Session = Depends(get_db)):
    return analytics_mod.get_by_status(db)

@app.get("/analytics/trends")
def analytics_trends(db: Session = Depends(get_db)):
    return analytics_mod.get_trends(db)

@app.get("/analytics/by-platform")
def analytics_by_platform(db: Session = Depends(get_db)):
    return analytics_mod.get_by_platform(db)

@app.get("/analytics/by-dev-type")
def analytics_by_dev_type(db: Session = Depends(get_db)):
    return analytics_mod.get_by_dev_type(db)

@app.get("/analytics/by-chatbot")
def analytics_by_chatbot(db: Session = Depends(get_db)):
    return analytics_mod.get_by_chatbot(db)


@app.get("/cases/export")
def export_cases_csv(db: Session = Depends(get_db)):
    cases = crud.get_cases(db, skip=0, limit=10000)
    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["ID","Owner","Job Level","Program/Team","Title","Problem Statement","Solution Description",
               "AI Technique","Tools/Services","Key Prompts","Output/Outcome",
               "Time Saved %","Yearly HC Saved","Accuracy %","Cost Reduction %","Yearly USD Saved",
               "Dev Time Hours","Status","Scalability","Innovation","Date Created"]
    writer.writerow(headers)
    for c in cases:
        writer.writerow([c.id, c.owner_login, c.job_level, c.program_team, c.use_case_title,
            c.problem_statement, c.solution_description, c.ai_technique, c.tools_services,
            c.key_prompts, c.output_outcome, c.time_saved, c.yearly_hc_saved,
            c.accuracy, c.cost_reduction, c.yearly_usd_saved, c.dev_time_hours, c.status,
            c.scalability_score, c.innovation_score, c.date_created])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ai_cases_export.csv"})


@app.get("/cases/count")
def count_cases(
    program_team: Optional[str] = None,
    ai_technique: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    total = crud.count_cases(db, program_team, ai_technique, status)
    return {"total": total}


@app.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    db_case = crud.get_case(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case


@app.put("/cases/{case_id}", response_model=CaseResponse)
def update_case(case_id: str, case_update: CaseUpdate, db: Session = Depends(get_db), user: User = Depends(require_user)):
    db_case = crud.get_case(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    if user.role != "admin" and db_case.owner_login != user.login:
        raise HTTPException(status_code=403, detail="You can only edit your own cases")
    return crud.update_case(db, case_id, case_update)


@app.delete("/cases/{case_id}")
def delete_case(case_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    db_case = crud.get_case(db, case_id)
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    if user.role != "admin" and db_case.owner_login != user.login:
        raise HTTPException(status_code=403, detail="You can only delete your own cases")
    crud.delete_case(db, case_id)
    return {"detail": "Case deleted"}


# Serve frontend static files
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
