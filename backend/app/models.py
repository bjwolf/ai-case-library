import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    login = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="learner")  # learner, admin
    is_active = Column(Boolean, default=True)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_login = Column(String, nullable=False)
    job_level = Column(String, nullable=True)
    program_team = Column(String, nullable=False)
    use_case_title = Column(String, nullable=False)
    problem_statement = Column(Text, nullable=False)
    ai_technique = Column(String, nullable=False)
    tools_services = Column(String, nullable=True)
    key_prompts = Column(Text, nullable=True)
    input_data = Column(Text, nullable=True)
    output_outcome = Column(Text, nullable=True)
    solution_description = Column(Text, nullable=True)
    time_saved = Column(Float, nullable=True)
    yearly_hc_saved = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    cost_reduction = Column(Float, nullable=True)
    yearly_usd_saved = Column(Float, nullable=True)
    dev_time_hours = Column(Float, nullable=True)
    status = Column(String, default="Developing")
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    date_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))
    rank = Column(Integer, nullable=True)
    scalability_score = Column(Float, nullable=True)
    innovation_score = Column(Float, nullable=True)
