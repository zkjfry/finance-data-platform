import { apiClient } from "./client";

export type SearchCompanyResult = {
  type: "company";
  id: number;
  company_name: string;
  legal_name?: string | null;
  description?: string | null;
  sector?: string | null;
  industry?: string | null;
  country?: string | null;
  website?: string | null;
  ticker?: string | null;
  exchange?: string | null;
  currency?: string | null;
  security_type?: string | null;
};

export type SearchNewsResult = {
  type: "news";
  id: number;
  source?: string | null;
  article_id?: string | null;
  title: string;
  url?: string | null;
  published_at?: string | null;
  ticker?: string | null;
  summary?: string | null;
  relevance?: number;
};

export type SearchReportResult = {
  type: "report";
  id: number;
  source?: string | null;
  report_id?: string | null;
  company_name?: string | null;
  ticker?: string | null;
  title: string;
  report_type?: string | null;
  url?: string | null;
  detail_url?: string | null;
  pdf_url?: string | null;
  published_at?: string | null;
  summary?: string | null;
  relevance?: number;
};

export type GlobalSearchResponse = {
  keyword: string;
  companies: SearchCompanyResult[];
  news: SearchNewsResult[];
  reports: SearchReportResult[];
  total: number;
};

export async function globalSearch(keyword: string): Promise<GlobalSearchResponse> {
  const response = await apiClient.get("/search", {
    params: {
      q: keyword,
      limit: 8,
    },
  });

  return response.data.data;
}