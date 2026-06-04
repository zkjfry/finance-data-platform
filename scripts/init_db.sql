CREATE TABLE IF NOT EXISTS raw_documents (
    id SERIAL PRIMARY KEY,
    source VARCHAR(128) NOT NULL,
    source_type VARCHAR(128) NOT NULL,
    url TEXT NOT NULL,
    content_type VARCHAR(64) NOT NULL,
    content_hash VARCHAR(128) NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    local_path TEXT,
    raw_text TEXT
);

CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    source VARCHAR(128) NOT NULL,
    article_id VARCHAR(256) NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    symbols TEXT,
    authors TEXT,
    summary TEXT,
    body_text TEXT,
    content_hash VARCHAR(128) NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_news_source_article_id UNIQUE (source, article_id)
);

CREATE TABLE IF NOT EXISTS research_reports (
    id SERIAL PRIMARY KEY,
    source VARCHAR(128) NOT NULL,
    report_id VARCHAR(256) NOT NULL,
    company_name VARCHAR(256),
    ticker VARCHAR(64),
    title TEXT NOT NULL,
    report_type VARCHAR(128),
    published_at TIMESTAMPTZ,
    authors TEXT,
    detail_url TEXT,
    pdf_url TEXT,
    pdf_local_path TEXT,
    summary TEXT,
    body_text TEXT,
    content_hash VARCHAR(128) NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_reports_source_report_id UNIQUE (source, report_id)
);

CREATE TABLE IF NOT EXISTS crawl_state (
    id SERIAL PRIMARY KEY,
    source VARCHAR(128) NOT NULL,
    target_key VARCHAR(256) NOT NULL,
    last_fetched_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_content_hash VARCHAR(128),
    status VARCHAR(64),
    error_message TEXT,
    CONSTRAINT uq_crawl_state_source_target UNIQUE (source, target_key)
);

-- Phase 1: crawl run logging

CREATE TABLE IF NOT EXISTS crawl_runs (
    id SERIAL PRIMARY KEY,
    crawler_name VARCHAR(128) NOT NULL,
    source VARCHAR(128) NOT NULL,
    status VARCHAR(64) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NULL,
    items_fetched INTEGER NOT NULL DEFAULT 0,
    items_inserted INTEGER NOT NULL DEFAULT 0,
    items_skipped INTEGER NOT NULL DEFAULT 0,
    items_failed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_source
ON crawl_runs (source);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_status
ON crawl_runs (status);

CREATE INDEX IF NOT EXISTS idx_crawl_runs_started_at
ON crawl_runs (started_at DESC);


-- Phase 1: search/filter indexes

CREATE INDEX IF NOT EXISTS idx_news_articles_published_at
ON news_articles (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_articles_source
ON news_articles (source);

CREATE INDEX IF NOT EXISTS idx_news_articles_updated_at
ON news_articles (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_articles_content_hash
ON news_articles (content_hash);

CREATE INDEX IF NOT EXISTS idx_news_articles_symbols
ON news_articles (symbols);

CREATE INDEX IF NOT EXISTS idx_news_articles_fts
ON news_articles
USING GIN (
    to_tsvector(
        'english',
        coalesce(title, '') || ' ' ||
        coalesce(summary, '') || ' ' ||
        coalesce(body_text, '') || ' ' ||
        coalesce(symbols, '')
    )
);


CREATE INDEX IF NOT EXISTS idx_research_reports_published_at
ON research_reports (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_reports_source
ON research_reports (source);

CREATE INDEX IF NOT EXISTS idx_research_reports_ticker
ON research_reports (ticker);

CREATE INDEX IF NOT EXISTS idx_research_reports_company_name
ON research_reports (company_name);

CREATE INDEX IF NOT EXISTS idx_research_reports_updated_at
ON research_reports (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_reports_content_hash
ON research_reports (content_hash);

CREATE INDEX IF NOT EXISTS idx_research_reports_fts
ON research_reports
USING GIN (
    to_tsvector(
        'english',
        coalesce(title, '') || ' ' ||
        coalesce(summary, '') || ' ' ||
        coalesce(body_text, '') || ' ' ||
        coalesce(company_name, '') || ' ' ||
        coalesce(ticker, '') || ' ' ||
        coalesce(report_type, '')
    )
);

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(256) NOT NULL,
    legal_name VARCHAR(256),
    description TEXT,
    sector VARCHAR(128),
    industry VARCHAR(128),
    country VARCHAR(64),
    website TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_companies_canonical_name UNIQUE (canonical_name)
);

CREATE TABLE IF NOT EXISTS securities (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    ticker VARCHAR(64) NOT NULL,
    exchange VARCHAR(64),
    currency VARCHAR(16),
    security_type VARCHAR(64) NOT NULL DEFAULT 'equity',
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_securities_ticker_exchange UNIQUE (ticker, exchange)
);

CREATE TABLE IF NOT EXISTS company_aliases (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    alias VARCHAR(256) NOT NULL,
    alias_type VARCHAR(64) NOT NULL DEFAULT 'name',
    inserted_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_company_aliases_alias UNIQUE (alias)
);

CREATE TABLE IF NOT EXISTS market_prices (
    id SERIAL PRIMARY KEY,
    security_id INTEGER NOT NULL REFERENCES securities(id),
    price_date DATE NOT NULL,
    open NUMERIC(18, 6),
    high NUMERIC(18, 6),
    low NUMERIC(18, 6),
    close NUMERIC(18, 6),
    adj_close NUMERIC(18, 6),
    volume BIGINT,
    source VARCHAR(128) NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_market_prices_security_date UNIQUE (security_id, price_date)
);

CREATE INDEX IF NOT EXISTS idx_companies_canonical_name
ON companies (canonical_name);

CREATE INDEX IF NOT EXISTS idx_company_aliases_alias
ON company_aliases (alias);

CREATE INDEX IF NOT EXISTS idx_securities_ticker
ON securities (ticker);

CREATE INDEX IF NOT EXISTS idx_securities_company_id
ON securities (company_id);

CREATE INDEX IF NOT EXISTS idx_market_prices_security_date
ON market_prices (security_id, price_date DESC);

CREATE INDEX IF NOT EXISTS idx_market_prices_source
ON market_prices (source);

CREATE TABLE IF NOT EXISTS document_company_links (
    id SERIAL PRIMARY KEY,
    document_type VARCHAR(32) NOT NULL,
    document_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    security_id INTEGER REFERENCES securities(id),
    ticker VARCHAR(64),
    match_method VARCHAR(64) NOT NULL,
    evidence_text TEXT,
    review_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    confidence NUMERIC(5, 4) NOT NULL,
    inserted_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_document_company_link_document_company
        UNIQUE (document_type, document_id, company_id)
);

CREATE INDEX IF NOT EXISTS idx_document_company_links_document
ON document_company_links (document_type, document_id);

CREATE INDEX IF NOT EXISTS idx_document_company_links_company
ON document_company_links (company_id);

CREATE INDEX IF NOT EXISTS idx_document_company_links_security
ON document_company_links (security_id);

CREATE INDEX IF NOT EXISTS idx_document_company_links_ticker
ON document_company_links (ticker);

CREATE INDEX IF NOT EXISTS idx_document_company_links_review_status
ON document_company_links (review_status);

CREATE INDEX IF NOT EXISTS idx_document_company_links_company_status
ON document_company_links (company_id, review_status);