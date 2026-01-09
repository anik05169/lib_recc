// api.js

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
});

export const getBooks = () => api.get("/books");
export const trainModel = () => api.post("/train");
export const recommendBooks = (bookId) =>
  api.get(`/recommend/${bookId}`);

