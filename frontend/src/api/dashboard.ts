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
  items_failed: number;
  started_at?: string | null;
};

export type DashboardSummary = {
  counts: DashboardCounts;
  latest_crawl_runs: CrawlRun[];
};

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await apiClient.get("/dashboard/summary");
  return response.data.data;
}