import axios from "axios";

const TOKEN_KEY = "daily-random-events-token";
const USER_KEY = "daily-random-events-user";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, 
});

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function getStoredUser() {
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    window.localStorage.removeItem(USER_KEY);
    return null;
  }
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

export async function requestPasswordReset(email) {
  const response = await api.post("/auth/password-reset/", { email });
  return response.data;
}

export async function confirmPasswordReset(payload) {
  const response = await api.post("/auth/password-reset-confirm/", payload);
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

export async function fetchLogs(page = 1, status = "ALL", q = "", sort = "newest") {
  const params = { page };
  if (status && status !== "ALL") {
    params.status = status;
  }
  if (q) {
    params.q = q;
  }
  if (sort && sort !== "newest") {
    params.sort = sort;
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

export async function fetchSaved(page = 1, q = "", sort = "newest") {
  const params = { page };
  if (q) {
    params.q = q;
  }
  if (sort && sort !== "newest") {
    params.sort = sort;
  }
  const response = await api.get("/saved/", { params });
  return response.data;
}

export async function createSaved(payload) {
  const response = await api.post("/saved/", payload);
  return response.data;
}

export async function deleteSaved(savedId) {
  await api.delete(`/saved/${savedId}/`);
}

export async function fetchAdminActivities(page = 1) {
  const response = await api.get("/admin/activities/", {
    params: { page },
  });
  return response.data;
}

export async function createAdminActivity(payload) {
  const response = await api.post("/admin/activities/", payload);
  return response.data;
}

export async function updateAdminActivity(activityId, payload) {
  const response = await api.patch(`/admin/activities/${activityId}/`, payload);
  return response.data;
}

export async function deleteAdminActivity(activityId) {
  await api.delete(`/admin/activities/${activityId}/`);
}

export async function importAdminActivitiesCsv(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/admin/activities/import-csv/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export async function fetchAdminAuditLogs(page = 1) {
  const response = await api.get("/admin/audit-logs/", {
    params: { page },
  });
  return response.data;
}
