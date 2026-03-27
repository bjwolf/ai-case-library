from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    owner_login: Optional[str] = None
    job_level: Optional[str] = None
    program_team: str
    use_case_title: str
    problem_statement: str
    ai_technique: str
    platform: Optional[str] = None
    dev_type: Optional[str] = None
    is_chatbot: Optional[str] = None
    tools_services: Optional[str] = None
    key_prompts: Optional[str] = None
    output_outcome: Optional[str] = None
    solution_description: Optional[str] = None
    time_saved: Optional[float] = None
    yearly_hc_saved: Optional[float] = None
    accuracy: Optional[float] = None
    cost_reduction: Optional[float] = None
    yearly_usd_saved: Optional[float] = None
    dev_time_hours: Optional[float] = None
    status: str = Field(default="Developing", pattern="^(Developing|UAT|In Production)$")
    scalability_score: Optional[float] = None
    innovation_score: Optional[float] = None


class CaseUpdate(BaseModel):
    owner_login: Optional[str] = None
    job_level: Optional[str] = None
    program_team: Optional[str] = None
    use_case_title: Optional[str] = None
    problem_statement: Optional[str] = None
    ai_technique: Optional[str] = None
    platform: Optional[str] = None
    dev_type: Optional[str] = None
    is_chatbot: Optional[str] = None
    tools_services: Optional[str] = None
    key_prompts: Optional[str] = None
    output_outcome: Optional[str] = None
    solution_description: Optional[str] = None
    time_saved: Optional[float] = None
    yearly_hc_saved: Optional[float] = None
    accuracy: Optional[float] = None
    cost_reduction: Optional[float] = None
    yearly_usd_saved: Optional[float] = None
    dev_time_hours: Optional[float] = None
    status: Optional[str] = Field(default=None, pattern="^(Developing|UAT|In Production)$")
    scalability_score: Optional[float] = None
    innovation_score: Optional[float] = None


class CaseResponse(BaseModel):
    id: str
    owner_login: str
    job_level: Optional[str]
    program_team: str
    use_case_title: str
    problem_statement: str
    ai_technique: str
    platform: Optional[str]
    dev_type: Optional[str]
    is_chatbot: Optional[str]
    tools_services: Optional[str]
    key_prompts: Optional[str]
    output_outcome: Optional[str]
    solution_description: Optional[str]
    time_saved: Optional[float]
    yearly_hc_saved: Optional[float]
    accuracy: Optional[float]
    cost_reduction: Optional[float]
    yearly_usd_saved: Optional[float]
    dev_time_hours: Optional[float]
    status: str
    date_created: datetime
    date_updated: datetime
    rank: Optional[int]
    scalability_score: Optional[float]
    innovation_score: Optional[float]

    model_config = {"from_attributes": True}
