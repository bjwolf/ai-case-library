from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import Optional
from app.models import Case
from app.schemas import CaseCreate, CaseUpdate


def create_case(db: Session, case: CaseCreate) -> Case:
    db_case = Case(**case.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def get_case(db: Session, case_id: str) -> Optional[Case]:
    return db.query(Case).filter(Case.id == case_id).first()


def get_cases(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    program_team: Optional[str] = None,
    ai_technique: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = "date_created",
    order: str = "desc",
    owner_login: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Case]:
    query = db.query(Case)

    if program_team:
        query = query.filter(Case.program_team.ilike(f"%{program_team}%"))
    if ai_technique:
        query = query.filter(Case.ai_technique.ilike(f"%{ai_technique}%"))
    if status:
        query = query.filter(Case.status == status)
    if owner_login:
        query = query.filter(Case.owner_login == owner_login)
    if search:
        term = f"%{search}%"
        from sqlalchemy import or_
        query = query.filter(or_(
            Case.use_case_title.ilike(term),
            Case.problem_statement.ilike(term),
            Case.solution_description.ilike(term),
            Case.owner_login.ilike(term),
            Case.tools_services.ilike(term),
            Case.ai_technique.ilike(term),
            Case.program_team.ilike(term),
        ))

    sort_column = getattr(Case, sort_by, Case.date_created)
    query = query.order_by(desc(sort_column) if order == "desc" else asc(sort_column))

    return query.offset(skip).limit(limit).all()


def count_cases(
    db: Session,
    program_team: Optional[str] = None,
    ai_technique: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    query = db.query(Case)
    if program_team:
        query = query.filter(Case.program_team.ilike(f"%{program_team}%"))
    if ai_technique:
        query = query.filter(Case.ai_technique.ilike(f"%{ai_technique}%"))
    if status:
        query = query.filter(Case.status == status)
    return query.count()


def update_case(db: Session, case_id: str, case_update: CaseUpdate) -> Optional[Case]:
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        return None
    update_data = case_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_case, key, value)
    db.commit()
    db.refresh(db_case)
    return db_case


def delete_case(db: Session, case_id: str) -> bool:
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case:
        return False
    db.delete(db_case)
    db.commit()
    return True
