from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MetricComparison(BaseModel):
    company_value: Optional[float] = None
    sector_average: Optional[float] = None
    rank: Optional[int] = None
    percentile: Optional[float] = None
    total_peers: Optional[int] = None

class SectorThesisVerdict(BaseModel):
    verdict: str
    rationale: str
    key_observations: List[str]

class SectorComparisonResponse(BaseModel):
    symbol: str
    pe_comparison: Optional[MetricComparison] = None
    ev_ebitda_comparison: Optional[MetricComparison] = None
    pb_comparison: Optional[MetricComparison] = None
    roe_comparison: Optional[MetricComparison] = None
    revenue_growth_comparison: Optional[MetricComparison] = None
    sector_thesis: Optional[SectorThesisVerdict] = None
    generated_at: datetime
