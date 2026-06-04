import { apiClient } from "./client";

export async function searchCompanies(keyword: string) {
  const response = await apiClient.get("/companies/search", {
    params: { keyword },
  });
  return response.data.data;
}

export async function getCompanyOverview(tickerOrAlias: string) {
  const response = await apiClient.get(`/companies/${tickerOrAlias}`);
  return response.data.data;
}

export async function getCompanyPrices(tickerOrAlias: string) {
  const response = await apiClient.get(`/companies/${tickerOrAlias}/prices`);
  return response.data.data;
}