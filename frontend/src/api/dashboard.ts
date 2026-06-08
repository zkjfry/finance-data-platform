import { apiClient } from "./client";

export type DashboardCounts = {
  companies?: number;
  securities?: number;
  news_articles?: number;
  research_reports?: number;
  market_prices?: number;
  document_company_links?: number;
  accepted_document_links?: number;
  pending_document_links?: number;
};

export type CrawlRun = {
  id: number;
  crawler_name: string;
  source: string;
  status: string;
  items_fetched: number;
  items_inserted: number;
  items_skipped?: number;
  items_failed: number;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string | null;
};

export type SparklinePoint = {
  date?: string | null;
  close?: number | null;
};

export type MarketDashboardItem = {
  ticker: string;
  company_name: string;
  exchange?: string | null;
  currency?: string | null;
  sector?: string | null;
  industry?: string | null;
  price_date?: string | null;
  close?: number | null;
  previous_close?: number | null;
  change?: number | null;
  change_pct?: number | null;
  sparkline?: SparklinePoint[];
};

export type DashboardNewsItem = {
  id: number;
  source?: string | null;
  article_id?: string | null;
  url?: string | null;
  title: string;
  published_at?: string | null;
  summary?: string | null;
};

export type DashboardReportItem = {
  id: number;
  source?: string | null;
  report_id?: string | null;
  company_name?: string | null;
  ticker?: string | null;
  title: string;
  report_type?: string | null;
  published_at?: string | null;
  detail_url?: string | null;
  pdf_url?: string | null;
  summary?: string | null;
};

export type DashboardSummary = {
  counts: DashboardCounts;
  market_overview: MarketDashboardItem[];
  top_movers: MarketDashboardItem[];
  latest_news: DashboardNewsItem[];
  recent_reports: DashboardReportItem[];
  heatmap: MarketDashboardItem[];
  latest_crawl_runs: CrawlRun[];
};

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await apiClient.get("/dashboard/summary");
  return response.data.data;
}