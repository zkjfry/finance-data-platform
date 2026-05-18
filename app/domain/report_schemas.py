from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ResearchReport(BaseModel):
    source: str
    report_id: str
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    title: str
    report_type: Optional[str] = None
    published_at: Optional[datetime] = None
    authors: List[str] = Field(default_factory=list)
    detail_url: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_local_path: Optional[str] = None
    summary: Optional[str] = None
    body_text: Optional[str] = None
    content_hash: str
    inserted_at: datetime
    updated_at: datetime