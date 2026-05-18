from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    source: str
    article_id: str
    url: str
    title: str
    published_at: Optional[datetime] = None
    symbols: List[str] = Field(default_factory=list)
    authors: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    body_text: Optional[str] = None
    content_hash: str
    inserted_at: datetime
    updated_at: datetime