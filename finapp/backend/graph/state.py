from typing import TypedDict, Optional, List, Dict, Any
from ..models import Financials, Ratios, Issue

class AppState(TypedDict, total=False):
    run_id: str
    doc_id: str
    doc_path: str
    gcs_uri: Optional[str]
    gcs_mime: Optional[str]
    text: Optional[str]
    tables: Optional[list]
    financials: Optional[Financials]
    ratios: Optional[Ratios]
    issues: List[Issue]
    need_review: bool
    human_feedback: Dict[str, Any]
    audit: List[Dict[str, Any]]
    confidence_thresholds: Dict[str, float]
