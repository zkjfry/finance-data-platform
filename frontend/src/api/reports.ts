import { apiClient } from "./client";

export type ResearchReport = {
  id: number;
  source?: string | null;
  report_id?: string | null;
  company_name?: string | null;
  ticker?: string | null;
  title: string;
  report_type?: string | null;
  published_at?: string | null;
  authors?: string[];
  detail_url?: string | null;
  pdf_url?: string | null;
  summary?: string | null;
  body_text?: string | null;
  updated_at?: string;
  relevance?: number;
};

export type ReportSearchParams = {
  keyword?: string;
  ticker?: string;
  report_type?: string;
  source?: string;
  limit?: number;
  offset?: number;
};

export type ReportSearchResponse = {
  data: ResearchReport[];
  meta: {
    limit: number;
    offset: number;
    total: number;
  };
};

export async function getLatestReports(limit = 10): Promise<ResearchReport[]> {
  const response = await apiClient.get("/reports/latest", {
    params: { limit },
  });

  return response.data.data;
}

export async function searchReports(
  params: ReportSearchParams
): Promise<ReportSearchResponse> {
  const response = await apiClient.get("/reports", {
    params: {
      keyword: params.keyword || undefined,
      ticker: params.ticker || undefined,
      report_type: params.report_type || undefined,
      source: params.source || undefined,
      limit: params.limit ?? 20,
      offset: params.offset ?? 0,
    },
  });

  return {
    data: response.data.data,
    meta: response.data.meta,
  };
}