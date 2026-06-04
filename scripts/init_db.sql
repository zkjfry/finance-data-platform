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