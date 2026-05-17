import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to add a mock token if needed
api.interceptors.request.use((config) => {
  // In development, the backend bypasses JWT.
  // We attach a dummy token so the OAuth2 dependency doesn't crash on missing header.
  config.headers.Authorization = `Bearer dummy-token`;
  return config;
});
