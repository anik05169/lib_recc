import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

export const getBooks = () => api.get("/books");
export const trainModel = () => api.post("/train");
export const recommendBooks = (bookId) =>
  api.get(`/recommend/${bookId}`);
