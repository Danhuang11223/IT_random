import axios from "axios";

const TOKEN_KEY = "daily-random-events-token";
const USER_KEY = "daily-random-events-user";

export const api = axios.create({
  baseURL: "/api",
});

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function getStoredUser() {
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function clearSession() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  delete api.defaults.headers.common.Authorization;
}

export function setSession(token, user) {
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  api.defaults.headers.common.Authorization = `Token ${token}`;
}

const existingToken = getStoredToken();
if (existingToken) {
  api.defaults.headers.common.Authorization = `Token ${existingToken}`;
}

export async function login(credentials) {
  const response = await api.post("/auth/login/", credentials);
  setSession(response.data.token, response.data.user);
  return response.data;
}

export async function register(payload) {
  const response = await api.post("/auth/register/", payload);
  setSession(response.data.token, response.data.user);
  return response.data;
}

export async function fetchMetadata() {
  const response = await api.get("/metadata/");
  return response.data;
}

export async function generateActivity(payload) {
  const response = await api.post("/generate/", payload);
  return response.data;
}

export async function rerollActivity(requestId) {
  const response = await api.post(`/generate/${requestId}/reroll/`);
  return response.data;
}

export async function acceptSuggestion(suggestionId) {
  const response = await api.post(`/suggestions/${suggestionId}/accept/`);
  return response.data;
}

export async function fetchLogs(page = 1, status = "ALL") {
  const params = { page };
  if (status && status !== "ALL") {
    params.status = status;
  }

  const response = await api.get("/logs/", {
    params,
  });
  return response.data;
}

export async function createLog(payload) {
  const response = await api.post("/logs/", payload);
  return response.data;
}

export async function deleteLog(logId) {
  await api.delete(`/logs/${logId}/`);
}
