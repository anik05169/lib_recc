// api.js — shared API configuration

const rawUrl = import.meta.env.VITE_API_BASE_URL;

export const isApiConfigured = Boolean(rawUrl);
export const API_BASE_URL = rawUrl ? rawUrl.replace(/\/$/, "") : "";
export const PLACEHOLDER_IMAGE_URL = "https://placehold.co/150x200?text=No+Image";

export function getApiBaseUrl() {
  if (!API_BASE_URL) {
    throw new Error("VITE_API_BASE_URL is not defined. Copy frontend/.env.example to .env");
  }
  return API_BASE_URL;
}
