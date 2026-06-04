import { apiClient } from "./client";

export type NewsArticle = {
  id: number;
  source?: string | null;
  article_id?: string | null;
  url?: string | null;
  title: string;
  published_at?: string | null;
  symbols?: string[];
  authors?: string[];
  summary?: string | null;
  body_text?: string | null;
  updated_at?: string;
  relevance?: number;
};

export type NewsSearchParams = {
  keyword?: string;
  symbol?: string;
  source?: string;
  limit?: number;
  offset?: number;
};

export type NewsSearchResponse = {
  data: NewsArticle[];
  meta: {
    limit: number;
    offset: number;
    total: number;
  };
};

export async function getLatestNews(limit = 10): Promise<NewsArticle[]> {
  const response = await apiClient.get("/news/latest", {
    params: { limit },
  });

  return response.data.data;
}

export async function searchNews(
  params: NewsSearchParams
): Promise<NewsSearchResponse> {
  const response = await apiClient.get("/news", {
    params: {
      keyword: params.keyword || undefined,
      symbol: params.symbol || undefined,
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