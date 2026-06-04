import json
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.time_utils import utc_now
from app.domain.company_schemas import DocumentCompanyLink
from app.infrastructure.storage.models import (
    CompanyAliasModel,
    CompanyModel,
    NewsArticleModel,
    ResearchReportModel,
    SecurityModel,
)
from app.pipeline.upsert import upsert_document_company_link


ACCEPTED_CONFIDENCE_THRESHOLD = 0.9
PENDING_CONFIDENCE_THRESHOLD = 0.6


class CompanyLinkCandidate:
    def __init__(
        self,
        company_id: int,
        security_id: int | None,
        ticker: str | None,
        alias: str,
    ) -> None:
        self.company_id = company_id
        self.security_id = security_id
        self.ticker = ticker
        self.alias = alias


class CompanyLinkMatch:
    def __init__(
        self,
        candidate: CompanyLinkCandidate,
        method: str,
        confidence: float,
        evidence_text: str | None,
    ) -> None:
        self.candidate = candidate
        self.method = method
        self.confidence = confidence
        self.evidence_text = evidence_text


class CompanyLinker:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.candidates = self._load_candidates()

    def run(self) -> dict:
        news_result = self.link_news_articles()
        report_result = self.link_research_reports()

        return {
            "status": "success",
            "news": news_result,
            "reports": report_result,
            "total_links_inserted_or_updated": (
                news_result["links_inserted_or_updated"]
                + report_result["links_inserted_or_updated"]
            ),
            "total_accepted_links": (
                news_result["accepted_links"]
                + report_result["accepted_links"]
            ),
            "total_pending_links": (
                news_result["pending_links"]
                + report_result["pending_links"]
            ),
            "total_skipped_low_confidence": (
                news_result["skipped_low_confidence"]
                + report_result["skipped_low_confidence"]
            ),
        }

    def link_news_articles(self) -> dict:
        rows = self.db.execute(
            select(NewsArticleModel).order_by(NewsArticleModel.id.asc())
        ).scalars().all()

        scanned = 0
        linked = 0
        accepted = 0
        pending = 0
        skipped_low_confidence = 0

        for row in rows:
            scanned += 1
            matches = self._match_news(row)

            for match in matches:
                if match.confidence < PENDING_CONFIDENCE_THRESHOLD:
                    skipped_low_confidence += 1
                    continue

                review_status = self._review_status(match.confidence)

                now = utc_now()
                link = DocumentCompanyLink(
                    document_type="news",
                    document_id=row.id,
                    company_id=match.candidate.company_id,
                    security_id=match.candidate.security_id,
                    ticker=match.candidate.ticker,
                    match_method=match.method,
                    evidence_text=match.evidence_text,
                    review_status=review_status,
                    confidence=Decimal(str(match.confidence)),
                    inserted_at=now,
                    updated_at=now,
                )
                upsert_document_company_link(self.db, link)

                linked += 1
                if review_status == "accepted":
                    accepted += 1
                elif review_status == "pending":
                    pending += 1

        return {
            "documents_scanned": scanned,
            "links_inserted_or_updated": linked,
            "accepted_links": accepted,
            "pending_links": pending,
            "skipped_low_confidence": skipped_low_confidence,
        }

    def link_research_reports(self) -> dict:
        rows = self.db.execute(
            select(ResearchReportModel).order_by(ResearchReportModel.id.asc())
        ).scalars().all()

        scanned = 0
        linked = 0
        accepted = 0
        pending = 0
        skipped_low_confidence = 0

        for row in rows:
            scanned += 1
            matches = self._match_report(row)

            for match in matches:
                if match.confidence < PENDING_CONFIDENCE_THRESHOLD:
                    skipped_low_confidence += 1
                    continue

                review_status = self._review_status(match.confidence)

                now = utc_now()
                link = DocumentCompanyLink(
                    document_type="report",
                    document_id=row.id,
                    company_id=match.candidate.company_id,
                    security_id=match.candidate.security_id,
                    ticker=match.candidate.ticker,
                    match_method=match.method,
                    evidence_text=match.evidence_text,
                    review_status=review_status,
                    confidence=Decimal(str(match.confidence)),
                    inserted_at=now,
                    updated_at=now,
                )
                upsert_document_company_link(self.db, link)

                linked += 1
                if review_status == "accepted":
                    accepted += 1
                elif review_status == "pending":
                    pending += 1

        return {
            "documents_scanned": scanned,
            "links_inserted_or_updated": linked,
            "accepted_links": accepted,
            "pending_links": pending,
            "skipped_low_confidence": skipped_low_confidence,
        }

    def _load_candidates(self) -> list[CompanyLinkCandidate]:
        rows = self.db.execute(
            select(CompanyModel, SecurityModel, CompanyAliasModel)
            .join(SecurityModel, SecurityModel.company_id == CompanyModel.id)
            .join(CompanyAliasModel, CompanyAliasModel.company_id == CompanyModel.id)
            .where(CompanyModel.is_active.is_(True))
        ).all()

        candidates: list[CompanyLinkCandidate] = []

        for company, security, alias in rows:
            candidates.append(
                CompanyLinkCandidate(
                    company_id=company.id,
                    security_id=security.id if security else None,
                    ticker=security.ticker if security else None,
                    alias=alias.alias,
                )
            )

        return candidates

    def _match_news(self, row: NewsArticleModel) -> list[CompanyLinkMatch]:
        matches: dict[int, CompanyLinkMatch] = {}

        symbols = self._json_list(row.symbols)
        symbols_upper = {item.upper() for item in symbols}

        searchable_text = self._join_text(
            row.title,
            row.summary,
            row.body_text,
        )

        for candidate in self.candidates:
            if candidate.ticker and candidate.ticker.upper() in symbols_upper:
                self._put_best_match(
                    matches=matches,
                    match=CompanyLinkMatch(
                        candidate=candidate,
                        method="news_symbols_ticker",
                        confidence=1.0,
                        evidence_text=f"symbols contains ticker {candidate.ticker}",
                    ),
                )
                continue

            if candidate.alias and self._contains_alias(searchable_text, candidate.alias):
                confidence = self._alias_confidence(candidate.alias)
                evidence = self._build_alias_evidence(
                    text=searchable_text,
                    alias=candidate.alias,
                )
                self._put_best_match(
                    matches=matches,
                    match=CompanyLinkMatch(
                        candidate=candidate,
                        method="news_body_alias",
                        confidence=confidence,
                        evidence_text=evidence,
                    ),
                )

        return list(matches.values())

    def _match_report(self, row: ResearchReportModel) -> list[CompanyLinkMatch]:
        matches: dict[int, CompanyLinkMatch] = {}

        report_ticker = row.ticker.upper().strip() if row.ticker else None
        company_name_text = self._join_text(row.company_name)
        searchable_text = self._join_text(
            row.title,
            row.company_name,
            row.summary,
            row.body_text,
        )

        for candidate in self.candidates:
            if (
                report_ticker
                and candidate.ticker
                and report_ticker == candidate.ticker.upper()
            ):
                self._put_best_match(
                    matches=matches,
                    match=CompanyLinkMatch(
                        candidate=candidate,
                        method="report_ticker",
                        confidence=1.0,
                        evidence_text=f"report.ticker equals {candidate.ticker}",
                    ),
                )
                continue

            if candidate.alias and self._contains_alias(company_name_text, candidate.alias):
                evidence = self._build_alias_evidence(
                    text=company_name_text,
                    alias=candidate.alias,
                )
                self._put_best_match(
                    matches=matches,
                    match=CompanyLinkMatch(
                        candidate=candidate,
                        method="report_company_name_alias",
                        confidence=0.95,
                        evidence_text=evidence,
                    ),
                )
                continue

            if candidate.alias and self._contains_alias(searchable_text, candidate.alias):
                confidence = self._alias_confidence(candidate.alias)
                evidence = self._build_alias_evidence(
                    text=searchable_text,
                    alias=candidate.alias,
                )
                self._put_best_match(
                    matches=matches,
                    match=CompanyLinkMatch(
                        candidate=candidate,
                        method="report_body_alias",
                        confidence=confidence,
                        evidence_text=evidence,
                    ),
                )

        return list(matches.values())

    @staticmethod
    def _put_best_match(
        matches: dict[int, CompanyLinkMatch],
        match: CompanyLinkMatch,
    ) -> None:
        existing = matches.get(match.candidate.company_id)

        if existing is None:
            matches[match.candidate.company_id] = match
            return

        if match.confidence > existing.confidence:
            matches[match.candidate.company_id] = match

    @staticmethod
    def _json_list(value: str | None) -> list[str]:
        if not value:
            return []

        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return []

        return []

    @staticmethod
    def _join_text(*values: str | None) -> str:
        return " ".join(value for value in values if value).lower()

    @staticmethod
    def _contains_alias(text: str, alias: str) -> bool:
        if not text or not alias:
            return False

        alias_lower = alias.lower().strip()

        if len(alias_lower) <= 1:
            return False

        return alias_lower in text

    @staticmethod
    def _alias_confidence(alias: str) -> float:
        alias_upper = alias.upper().strip()

        # Ticker-like aliases are strong, but weaker than explicit extracted symbols.
        if alias_upper.isalnum() and 1 <= len(alias_upper) <= 5:
            return 0.85

        # Full company names are usually reliable.
        if len(alias) >= 10:
            return 0.8

        # Short aliases like Apple / Tesla / Amazon can be ambiguous in normal text.
        return 0.65

    @staticmethod
    def _review_status(confidence: float) -> str:
        if confidence >= ACCEPTED_CONFIDENCE_THRESHOLD:
            return "accepted"

        return "pending"

    @staticmethod
    def _build_alias_evidence(text: str, alias: str, window: int = 80) -> str | None:
        if not text or not alias:
            return None

        alias_lower = alias.lower().strip()
        index = text.find(alias_lower)

        if index < 0:
            return None

        start = max(0, index - window)
        end = min(len(text), index + len(alias_lower) + window)

        evidence = text[start:end].strip()

        if start > 0:
            evidence = "..." + evidence

        if end < len(text):
            evidence = evidence + "..."

        return evidence