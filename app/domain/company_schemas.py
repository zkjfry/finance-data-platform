from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class Company(BaseModel):
    id: int | None = None
    canonical_name: str
    legal_name: Optional[str] = None
    description: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    is_active: bool = True
    inserted_at: datetime
    updated_at: datetime


class Security(BaseModel):
    id: int | None = None
    company_id: int
    ticker: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    security_type: str = "equity"
    is_primary: bool = True
    inserted_at: datetime
    updated_at: datetime


class CompanyAlias(BaseModel):
    id: int | None = None
    company_id: int
    alias: str
    alias_type: str = "name"
    inserted_at: datetime


class MarketPrice(BaseModel):
    security_id: int
    price_date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    adj_close: Optional[Decimal] = None
    volume: Optional[int] = None
    source: str
    inserted_at: datetime
    updated_at: datetime


class DocumentCompanyLink(BaseModel):
    id: int | None = None
    document_type: str
    document_id: int
    company_id: int
    security_id: Optional[int] = None
    ticker: Optional[str] = None
    match_method: str
    evidence_text: Optional[str] = None
    review_status: str = "pending"
    confidence: Decimal
    inserted_at: datetime
    updated_at: datetime
