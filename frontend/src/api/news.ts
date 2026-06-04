import { apiClient } from "./client";

export async function getLatestNews(limit = 10) {
  const response = await apiClient.get("/news/latest", {
    params: { limit },
  });
  return response.data.data;
}

export async function searchNews(keyword: string) {
  const response = await apiClient.get("/news/search", {
    params: { keyword },
  });
  return response.data.data;
}