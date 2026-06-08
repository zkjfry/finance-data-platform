import { apiClient } from "./client";

export type MarketSecurity = {
  company_id: number;
  company_name: string;
  legal_name?: string | null;
  sector?: string | null;
  industry?: string | null;
  country?: string | null;

  security_id: number;
  ticker: string;
  exchange?: string | null;
  currency?: string | null;
  security_type?: string | null;

  price_date?: string | null;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  close?: number | null;
  adj_close?: number | null;
  volume?: number | null;
  previous_close?: number | null;
  change?: number | null;
  change_pct?: number | null;
};

export type MarketSecuritiesParams = {
  keyword?: string;
  sector?: string;
  sort_by?: "ticker" | "company_name" | "sector" | "close" | "change_pct" | "volume";
  sort_dir?: "asc" | "desc";
  limit?: number;
  offset?: number;
};

export type MarketSecuritiesResponse = {
  data: MarketSecurity[];
  meta: {
    limit: number;
    offset: number;
    total: number;
    has_more: boolean;
  };
};

export async function getMarketSecurities(
  params: MarketSecuritiesParams = {}
): Promise<MarketSecuritiesResponse> {
  const response = await apiClient.get("/markets/securities", {
    params,
  });

  return {
    data: response.data.data,
    meta: response.data.meta,
  };
}