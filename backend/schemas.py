from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["ok", "warn", "danger"]


class SecuritiesCase(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_risk_level: str = Field(..., description="C1-C5")
    product_risk_level: str = Field(..., description="R1-R5")
    business_type: str
    investment_experience_years: float = Field(..., ge=0)
    age: int = Field(..., ge=0)
    assets_under_management: float = Field(..., ge=0)
    transaction_amount: float = Field(..., ge=0)
    trades_30d: int = Field(..., ge=0)
    net_inflow_30d: float = Field(default=0)
    material_text: str = Field(..., min_length=1)


class AgentFinding(BaseModel):
    agent: str
    title: str
    score: int = Field(..., ge=0, le=35)
    severity: Severity
    findings: list[str]
    evidence: list[str] = Field(default_factory=list)


class AuditResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str
    decision: str
    agent_results: list[AgentFinding]
    report: str
