import { apiClient } from "./client";

export type Company = {
  id: number;
  canonical_name: string;
  legal_name?: string | null;
  description?: string | null;
  sector?: string | null;
  industry?: string | null;
  country?: string | null;
  website?: string | null;
  is_active?: boolean;
  updated_at?: string;
};

export type Security = {
  id: number;
  company_id: number;
  ticker: string;
  exchange?: string | null;
  currency?: string | null;
  security_type?: string | null;
  is_primary?: boolean;
  updated_at?: string;
};

export type MarketPrice = {
  id: number;
  security_id: number;
  price_date: string;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  close?: number | null;
  adj_close?: number | null;
  volume?: number | null;
  source?: string | null;
  updated_at?: string;
};

export type CompanyLinkedNews = {
  id: number;
  source?: string | null;
  article_id?: string | null;
  url?: string | null;
  title: string;
  published_at?: string | null;
  symbols?: string[];
  authors?: string[];
  summary?: string | null;
  updated_at?: string;
};

export type CompanyLinkedReport = {
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
  updated_at?: string;
};

export type CompanySearchResult = {
  company: Company;
  primary_security: Security | null;
};

export type CompanyOverview = {
  company: Company;
  primary_security: Security | null;
  aliases: string[];
  latest_price: MarketPrice | null;
  latest_news: CompanyLinkedNews[];
  latest_reports: CompanyLinkedReport[];
  price_history: MarketPrice[];
};

export async function listCompanies(limit = 20): Promise<CompanySearchResult[]> {
  const response = await apiClient.get("/companies", {
    params: { limit },
  });

  return response.data.data;
}

export async function searchCompanies(keyword: string): Promise<CompanySearchResult[]> {
  const response = await apiClient.get("/companies/search", {
    params: { keyword },
  });

  return response.data.data;
}

export async function getCompanyOverview(
  tickerOrAlias: string
): Promise<CompanyOverview> {
  const response = await apiClient.get(`/companies/${tickerOrAlias}`, {
    params: {
      news_limit: 5,
      reports_limit: 5,
      prices_limit: 30,
    },
  });

  return response.data.data;
}

export async function getCompanyPrices(
  tickerOrAlias: string
): Promise<MarketPrice[]> {
  const response = await apiClient.get(`/companies/${tickerOrAlias}/prices`);
  return response.data.data;
}