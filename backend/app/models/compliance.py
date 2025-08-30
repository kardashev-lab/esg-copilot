from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SeverityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class GapStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class ComplianceCheckRequest(BaseModel):
    framework: str  # GRI, SASB, TCFD, CSRD
    company_documents: List[str] = []
    peer_reports: Optional[List[str]] = None
    focus_areas: Optional[List[str]] = None

class FrameworkRequirement(BaseModel):
    id: str
    title: str
    description: str
    category: str
    mandatory: bool = True
    version: Optional[str] = None

class ComplianceGap(BaseModel):
    requirement_id: str
    requirement_title: str
    severity: SeverityLevel
    description: str
    recommendation: str
    status: GapStatus = GapStatus.OPEN
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class ComplianceReport(BaseModel):
    framework: str
    company_documents: List[str]
    compliance_score: float
    total_requirements: int
    compliant_requirements: int
    gaps: List[ComplianceGap]
    recommendations: List[str]
    generated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class BenchmarkingResult(BaseModel):
    framework: str
    company_score: float
    peer_average: float
    industry_average: float
    top_performers: List[Dict[str, Any]]
    benchmarking_insights: List[str]
    recommendations: List[str]

class ComplianceTimeline(BaseModel):
    framework: str
    current_phase: str
    next_deadline: str
    timeline: List[Dict[str, Any]]
