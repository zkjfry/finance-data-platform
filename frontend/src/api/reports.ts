import { apiClient } from "./client";

export async function getLatestReports(limit = 10) {
  const response = await apiClient.get("/reports/latest", {
    params: { limit },
  });
  return response.data.data;
}

export async function searchReports(keyword: string) {
  const response = await apiClient.get("/reports/search", {
    params: { keyword },
  });
  return response.data.data;
}