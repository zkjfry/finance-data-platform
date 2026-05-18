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