from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models import Case


def get_summary(db: Session):
    result = db.query(
        func.count(Case.id).label("total"),
        func.sum(Case.yearly_hc_saved).label("total_hc_saved"),
        func.sum(Case.yearly_usd_saved).label("total_usd_saved"),
        func.avg(Case.accuracy).label("avg_accuracy"),
        func.sum(Case.dev_time_hours).label("total_dev_hours"),
        func.avg(Case.time_saved).label("avg_time_saved"),
        func.avg(Case.cost_reduction).label("avg_cost_reduction"),
    ).first()
    return {
        "total_initiatives": result.total or 0,
        "total_hc_saved": round(result.total_hc_saved or 0, 1),
        "total_usd_saved": round(result.total_usd_saved or 0, 2),
        "avg_accuracy": round(result.avg_accuracy or 0, 1),
        "total_dev_hours": round(result.total_dev_hours or 0, 1),
        "avg_time_saved": round(result.avg_time_saved or 0, 1),
        "avg_cost_reduction": round(result.avg_cost_reduction or 0, 1),
    }


def get_by_program(db: Session):
    rows = db.query(
        Case.program_team,
        func.count(Case.id).label("count"),
        func.avg(Case.time_saved).label("avg_time_saved"),
        func.avg(Case.cost_reduction).label("avg_cost_reduction"),
        func.avg(Case.accuracy).label("avg_accuracy"),
        func.sum(Case.yearly_usd_saved).label("total_usd_saved"),
        func.sum(Case.yearly_hc_saved).label("total_hc_saved"),
    ).group_by(Case.program_team).all()
    return [{"program": r.program_team, "count": r.count,
             "avg_time_saved": round(r.avg_time_saved or 0, 1),
             "avg_cost_reduction": round(r.avg_cost_reduction or 0, 1),
             "avg_accuracy": round(r.avg_accuracy or 0, 1),
             "total_usd_saved": round(r.total_usd_saved or 0, 2),
             "total_hc_saved": round(r.total_hc_saved or 0, 1),
             } for r in rows]


def get_by_technique(db: Session):
    rows = db.query(
        Case.ai_technique,
        func.count(Case.id).label("count"),
    ).group_by(Case.ai_technique).all()
    return [{"technique": r.ai_technique, "count": r.count} for r in rows]


def get_by_status(db: Session):
    rows = db.query(
        Case.status,
        func.count(Case.id).label("count"),
    ).group_by(Case.status).all()
    return [{"status": r.status, "count": r.count} for r in rows]


def get_trends(db: Session):
    rows = db.query(
        func.strftime("%Y-%m", Case.date_created).label("month"),
        func.count(Case.id).label("count"),
    ).group_by(func.strftime("%Y-%m", Case.date_created)).order_by("month").all()
    return [{"month": r.month, "count": r.count} for r in rows]


def get_by_platform(db: Session):
    rows = db.query(
        Case.platform,
        func.count(Case.id).label("count"),
    ).filter(Case.platform.isnot(None)).group_by(Case.platform).all()
    return [{"platform": r.platform or "Unknown", "count": r.count} for r in rows]


def get_by_dev_type(db: Session):
    rows = db.query(
        Case.dev_type,
        func.count(Case.id).label("count"),
    ).filter(Case.dev_type.isnot(None)).group_by(Case.dev_type).all()
    return [{"dev_type": r.dev_type or "Unknown", "count": r.count} for r in rows]


def get_by_chatbot(db: Session):
    rows = db.query(
        Case.is_chatbot,
        func.count(Case.id).label("count"),
    ).filter(Case.is_chatbot.isnot(None)).group_by(Case.is_chatbot).all()
    return [{"is_chatbot": r.is_chatbot or "Unknown", "count": r.count} for r in rows]
