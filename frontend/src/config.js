// API configuration
// Remove trailing slash if present to avoid double slashes in URLs
const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
export const API_BASE_URL = baseUrl.replace(/\/+$/, '');

