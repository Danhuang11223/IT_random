import { computed, reactive } from "vue";

import {
  acceptSuggestion,
  clearSession,
  createAdminActivity,
  createLog,
  createSaved,
  deleteAdminActivity,
  deleteLog as destroyLog,
  deleteSaved as destroySaved,
  fetchAdminActivities,
  fetchAdminAuditLogs,
  fetchLogs,
  fetchMetadata,
  fetchSaved,
  generateActivity,
  getStoredToken,
  getStoredUser,
  importAdminActivitiesCsv,
  login,
  register,
  rerollActivity,
  updateAdminActivity,
} from "./api";
import { getBudgetCap } from "./budgetOptions";

const UI_PREFS_KEY = "daily-random-events-ui-prefs";
const HISTORY_SORTS = new Set(["newest", "oldest", "title"]);
let undoAction = null;
let undoTimerId = null;

const initialConstraints = () => ({
  time_minutes: "",
  budget_preference: "",
  mood: "",
  social_preference: "",
  excluded_categories: [],
});

const initialCompletion = () => ({
  rating: "",
  comment: "",
});

const initialFormErrors = () => ({
  login: {},
  register: {},
  constraints: {},
  completion: {},
  saved: {},
  admin: {},
});

const initialPagination = (pageSize = 10) => ({
  count: 0,
  page: 1,
  page_size: pageSize,
  total_pages: 1,
  next: null,
  previous: null,
});

function loadStoredUiPrefs() {
  if (typeof window === "undefined") {
    return {
      reduceMotion: false,
      largerText: false,
      highContrast: false,
    };
  }

  const raw = window.localStorage.getItem(UI_PREFS_KEY);
  if (!raw) {
    return {
      reduceMotion: false,
      largerText: false,
      highContrast: false,
    };
  }

  try {
    const parsed = JSON.parse(raw);
    return {
      reduceMotion: Boolean(parsed?.reduceMotion),
      largerText: Boolean(parsed?.largerText),
      highContrast: Boolean(parsed?.highContrast),
    };
  } catch {
    return {
      reduceMotion: false,
      largerText: false,
      highContrast: false,
    };
  }
}

function persistUiPrefs(uiPrefs) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(UI_PREFS_KEY, JSON.stringify(uiPrefs));
}

function applyUiPrefsClasses(uiPrefs) {
  if (typeof document === "undefined") {
    return;
  }

  const body = document.body;
  body.classList.toggle("pref-reduce-motion", Boolean(uiPrefs.reduceMotion));
  body.classList.toggle("pref-large-text", Boolean(uiPrefs.largerText));
  body.classList.toggle("pref-high-contrast", Boolean(uiPrefs.highContrast));
}

const initialUiPrefs = loadStoredUiPrefs();
applyUiPrefsClasses(initialUiPrefs);

export const state = reactive({
  sessionToken: getStoredToken(),
  user: getStoredUser(),
  dashboardReady: false,
  metadata: {
    categories: [],
    moods: [],
    social_preferences: [],
  },
  constraints: initialConstraints(),
  completionForm: initialCompletion(),
  suggestion: null,
  pendingLog: null,
  historyItems: [],
  historyFilter: "ALL",
  historyQuery: "",
  historySort: "newest",
  pagination: initialPagination(10),
  savedItems: [],
  savedQuery: "",
  savedSort: "newest",
  savedPagination: initialPagination(10),
  adminAuditLogs: [],
  adminAuditPagination: initialPagination(20),
  uiPrefs: initialUiPrefs,
  message: "",
  error: "",
  retryAction: null,
  retryLabel: "",
  formErrors: initialFormErrors(),
  busy: {
    auth: false,
    dashboard: false,
    generate: false,
    accept: false,
    log: false,
    deleteLog: false,
    history: false,
    saved: false,
    admin: false,
    retry: false,
  },
  undo: {
    visible: false,
    label: "",
  },
});

export const isLoggedIn = computed(() => Boolean(state.sessionToken));
export const canReroll = computed(() => Boolean(state.suggestion?.request_id));
export const hasPendingAcceptedSuggestion = computed(() =>
  Boolean(state.pendingLog)
);

function buildPageItems(pagination, keyPrefix) {
  const totalPages = Math.max(1, Number(pagination.total_pages || 1));
  const currentPage = Math.min(
    totalPages,
    Math.max(1, Number(pagination.page || 1))
  );
  const items = [];

  const pushPage = (page) => {
    items.push({
      type: "page",
      value: page,
      key: `${keyPrefix}-page-${page}`,
    });
  };

  const pushEllipsis = (position) => {
    items.push({
      type: "ellipsis",
      value: "...",
      key: `${keyPrefix}-ellipsis-${position}`,
    });
  };

  if (totalPages <= 7) {
    for (let page = 1; page <= totalPages; page += 1) {
      pushPage(page);
    }
    return items;
  }

  if (currentPage <= 4) {
    for (let page = 1; page <= 5; page += 1) {
      pushPage(page);
    }
    pushEllipsis("right");
    pushPage(totalPages);
    return items;
  }

  if (currentPage >= totalPages - 3) {
    pushPage(1);
    pushEllipsis("left");
    for (let page = totalPages - 4; page <= totalPages; page += 1) {
      pushPage(page);
    }
    return items;
  }

  pushPage(1);
  pushEllipsis("left");
  for (let page = currentPage - 1; page <= currentPage + 1; page += 1) {
    pushPage(page);
  }
  pushEllipsis("right");
  pushPage(totalPages);
  return items;
}

export const historyPageNumbers = computed(() =>
  buildPageItems(state.pagination, "history")
);
export const savedPageNumbers = computed(() =>
  buildPageItems(state.savedPagination, "saved")
);

function resetFeedback() {
  state.completionForm = initialCompletion();
}

function createValidationError() {
  const error = new Error("validation_failed");
  error.isValidation = true;
  return error;
}

function clearRetry() {
  state.retryAction = null;
  state.retryLabel = "";
}

function clearUndo() {
  if (undoTimerId && typeof window !== "undefined") {
    window.clearTimeout(undoTimerId);
    undoTimerId = null;
  }
  undoAction = null;
  state.undo = {
    visible: false,
    label: "",
  };
}

function setUndo(label, action) {
  clearUndo();
  undoAction = action;
  state.undo = {
    visible: true,
    label,
  };
  if (typeof window !== "undefined") {
    undoTimerId = window.setTimeout(() => {
      clearUndo();
    }, 5000);
  }
}

function clearFormErrors(scope = null) {
  if (!scope) {
    state.formErrors = initialFormErrors();
    return;
  }

  state.formErrors = {
    ...state.formErrors,
    [scope]: {},
  };
}

function extractFieldErrors(responseData) {
  if (!responseData || typeof responseData !== "object") {
    return {};
  }

  const fieldErrors = {};

  if (Array.isArray(responseData.non_field_errors) && responseData.non_field_errors[0]) {
    fieldErrors._form = String(responseData.non_field_errors[0]);
  }

  for (const [key, value] of Object.entries(responseData)) {
    if (key === "detail" || key === "non_field_errors") {
      continue;
    }

    if (Array.isArray(value) && value.length) {
      fieldErrors[key] = String(value[0]);
    } else if (typeof value === "string" && value) {
      fieldErrors[key] = value;
    }
  }

  if (responseData?.detail && !Object.keys(fieldErrors).length) {
    fieldErrors._form = String(responseData.detail);
  }

  return fieldErrors;
}

function buildErrorMessage(responseData, fieldErrors) {
  if (responseData?.detail) {
    return String(responseData.detail);
  }

  if (fieldErrors._form) {
    return fieldErrors._form;
  }

  const fieldMessage = Object.entries(fieldErrors).find(([key]) => key !== "_form");
  if (fieldMessage) {
    return fieldMessage[1];
  }

  return "Request failed. Make sure the back end is running.";
}

function setInlineValidationErrors(scope, errors) {
  state.formErrors = {
    ...state.formErrors,
    [scope]: errors,
  };
  state.error = "";
  state.message = "";
  clearRetry();
}

function validateLoginCredentials(credentials) {
  const errors = {};

  if (!String(credentials.username || "").trim()) {
    errors.username = "Enter a username.";
  }

  if (!String(credentials.password || "").trim()) {
    errors.password = "Enter a password.";
  }

  return errors;
}

function validateRegisterPayload(payload) {
  const errors = {};
  const username = String(payload.username || "").trim();
  const email = String(payload.email || "").trim();
  const password = String(payload.password || "");

  if (!username) {
    errors.username = "Enter a username.";
  } else if (username.length < 3) {
    errors.username = "Username must be at least 3 characters.";
  }

  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = "Enter a valid email address.";
  }

  if (!password.trim()) {
    errors.password = "Enter a password.";
  } else if (password.length < 8) {
    errors.password = "Password must be at least 8 characters.";
  } else if (password.length > 128) {
    errors.password = "Password must be 128 characters or fewer.";
  }

  return errors;
}

function validateConstraints() {
  const errors = {};
  const rawTimeValue = String(state.constraints.time_minutes ?? "").trim();
  const timeValue = Number(rawTimeValue);

  if (!rawTimeValue) {
    errors.time_minutes = "Enter your available time.";
  } else if (!Number.isInteger(timeValue)) {
    errors.time_minutes = "Time must be a whole number of minutes.";
  } else if (timeValue < 5 || timeValue > 1440) {
    errors.time_minutes = "Time must be between 5 and 1440 minutes.";
  } else if (timeValue % 5 !== 0) {
    errors.time_minutes = "Use 5-minute increments.";
  }

  if (!String(state.constraints.budget_preference || "").trim()) {
    errors.budget_preference = "Choose a budget level.";
  }

  if (!String(state.constraints.mood || "").trim()) {
    errors.mood = "Choose how you feel today.";
  }

  if (!String(state.constraints.social_preference || "").trim()) {
    errors.social_preference = "Choose who is joining.";
  }

  return errors;
}

function validateCompletion(status) {
  const errors = {};
  const rawRating = String(state.completionForm.rating ?? "").trim();
  const commentValue = String(state.completionForm.comment || "");

  if (status === "COMPLETED" && rawRating) {
    const ratingValue = Number(rawRating);

    if (!Number.isInteger(ratingValue)) {
      errors.rating = "Rating must be a whole number.";
    } else if (ratingValue < 1 || ratingValue > 5) {
      errors.rating = "Rating must be between 1 and 5.";
    }
  }

  if (commentValue.length > 500) {
    errors.comment = "Comment must be 500 characters or fewer.";
  }

  return errors;
}

function resetSessionData() {
  state.dashboardReady = false;
  state.metadata = {
    categories: [],
    moods: [],
    social_preferences: [],
  };
  state.constraints = initialConstraints();
  state.suggestion = null;
  state.pendingLog = null;
  state.historyItems = [];
  state.historyFilter = "ALL";
  state.historyQuery = "";
  state.historySort = "newest";
  state.pagination = initialPagination(10);
  state.savedItems = [];
  state.savedQuery = "";
  state.savedSort = "newest";
  state.savedPagination = initialPagination(10);
  state.adminAuditLogs = [];
  state.adminAuditPagination = initialPagination(20);
  clearFormErrors();
  clearRetry();
  clearUndo();
  resetFeedback();
}

export function setNotice(text, options = {}) {
  const preserveUndo = Boolean(options.preserveUndo);
  state.message = text;
  state.error = "";
  clearRetry();
  if (!preserveUndo) {
    clearUndo();
  }
}

function setRetry(retryAction, retryLabel) {
  state.retryAction = retryAction || null;
  state.retryLabel = retryAction ? retryLabel || "Retry" : "";
}

function setRequestError(err, options = {}) {
  const { fieldScope = null, retryAction = null, retryLabel = "Retry" } = options;
  const responseData = err?.response?.data;
  const fieldErrors = extractFieldErrors(responseData);

  if (fieldScope) {
    state.formErrors = {
      ...state.formErrors,
      [fieldScope]: fieldErrors,
    };
  }

  state.error = buildErrorMessage(responseData, fieldErrors);
  state.message = "";
  setRetry(retryAction, retryLabel);
  clearUndo();
}

export function setError(err) {
  setRequestError(err);
}

function syncDefaults() {
  const moods = state.metadata.moods || [];
  const preferences = state.metadata.social_preferences || [];

  if (state.constraints.mood && !moods.includes(state.constraints.mood)) {
    state.constraints.mood = "";
  }

  if (
    state.constraints.social_preference &&
    !preferences.includes(state.constraints.social_preference)
  ) {
    state.constraints.social_preference = "";
  }
}

function updateHistory(logs) {
  const pageSize = state.pagination.page_size || 10;
  const totalPages = Math.max(1, Math.ceil((logs.count || 0) / pageSize));
  const page = Math.min(
    totalPages,
    Math.max(1, Number(logs.page || state.pagination.page || 1))
  );

  state.pendingLog = logs.pending || null;
  state.historyItems = logs.results || [];
  state.pagination = {
    count: logs.count || 0,
    page,
    page_size: pageSize,
    total_pages: totalPages,
    next: logs.next || null,
    previous: logs.previous || null,
  };
}

function updateSaved(saved) {
  const pageSize = state.savedPagination.page_size || 10;
  const totalPages = Math.max(1, Math.ceil((saved.count || 0) / pageSize));
  const page = Math.min(
    totalPages,
    Math.max(1, Number(saved.page || state.savedPagination.page || 1))
  );

  state.savedItems = saved.results || [];
  state.savedPagination = {
    count: saved.count || 0,
    page,
    page_size: pageSize,
    total_pages: totalPages,
    next: saved.next || null,
    previous: saved.previous || null,
  };
}

function updateAdminAudit(logs) {
  const pageSize = state.adminAuditPagination.page_size || 20;
  const totalPages = Math.max(1, Math.ceil((logs.count || 0) / pageSize));
  const page = Math.min(
    totalPages,
    Math.max(1, Number(logs.page || state.adminAuditPagination.page || 1))
  );

  state.adminAuditLogs = logs.results || [];
  state.adminAuditPagination = {
    count: logs.count || 0,
    page,
    page_size: pageSize,
    total_pages: totalPages,
    next: logs.next || null,
    previous: logs.previous || null,
  };
}

export async function loginWithPassword(credentials) {
  state.busy.auth = true;
  clearFormErrors("login");
  try {
    const validationErrors = validateLoginCredentials(credentials);
    if (Object.keys(validationErrors).length) {
      setInlineValidationErrors("login", validationErrors);
      throw createValidationError();
    }

    const payload = { ...credentials };
    const result = await login(payload);
    state.sessionToken = result.token;
    state.user = result.user;

    let dashboardLoaded = false;
    try {
      await loadDashboardData({ force: true });
      dashboardLoaded = true;
    } catch {
      // Keep auth success but preserve dashboard load error for retry.
    }

    if (dashboardLoaded) {
      setNotice(`Signed in as ${result.user.username}.`);
    }

    return {
      ...result,
      dashboardLoaded,
    };
  } catch (err) {
    if (err?.isValidation) {
      throw err;
    }

    setRequestError(err, {
      fieldScope: "login",
      retryAction: () => loginWithPassword({ ...credentials }),
      retryLabel: "Retry sign in",
    });
    throw err;
  } finally {
    state.busy.auth = false;
  }
}

export async function registerAccount(payload) {
  state.busy.auth = true;
  clearFormErrors("register");
  try {
    const validationErrors = validateRegisterPayload(payload);
    if (Object.keys(validationErrors).length) {
      setInlineValidationErrors("register", validationErrors);
      throw createValidationError();
    }

    const registerPayload = { ...payload };
    const result = await register(registerPayload);
    state.sessionToken = result.token;
    state.user = result.user;

    let dashboardLoaded = false;
    try {
      await loadDashboardData({ force: true });
      dashboardLoaded = true;
    } catch {
      // Keep auth success but preserve dashboard load error for retry.
    }

    if (dashboardLoaded) {
      setNotice(`Account created: ${result.user.username}.`);
    }

    return {
      ...result,
      dashboardLoaded,
    };
  } catch (err) {
    if (err?.isValidation) {
      throw err;
    }

    setRequestError(err, {
      fieldScope: "register",
      retryAction: () => registerAccount({ ...payload }),
      retryLabel: "Retry create account",
    });
    throw err;
  } finally {
    state.busy.auth = false;
  }
}

export function logout() {
  clearSession();
  state.sessionToken = "";
  state.user = null;
  resetSessionData();
  setNotice("Signed out.");
}

export async function loadDashboardData(options = {}) {
  if (state.dashboardReady && !options.force) {
    return;
  }

  state.busy.dashboard = true;
  try {
    const targetHistoryPage = Math.max(1, Number(options.historyPage || options.page || 1));
    const targetSavedPage = Math.max(1, Number(options.savedPage || 1));
    const [meta, logs, saved] = await Promise.all([
      fetchMetadata(),
      fetchLogs(
        targetHistoryPage,
        state.historyFilter,
        state.historyQuery,
        state.historySort
      ),
      fetchSaved(targetSavedPage, state.savedQuery, state.savedSort),
    ]);

    state.metadata = {
      categories: meta.categories || [],
      moods: meta.moods || [],
      social_preferences: meta.social_preferences || [],
    };
    syncDefaults();
    updateHistory({
      ...logs,
      page: targetHistoryPage,
    });
    updateSaved({
      ...saved,
      page: targetSavedPage,
    });

    state.dashboardReady = true;
    state.error = "";
    clearRetry();
  } catch (err) {
    state.dashboardReady = false;
    setRequestError(err, {
      retryAction: () => loadDashboardData({ force: true }),
      retryLabel: "Retry loading dashboard",
    });
    throw err;
  } finally {
    state.busy.dashboard = false;
  }
}

export async function loadHistoryPage(page = 1, options = {}) {
  const targetPage = Math.max(1, Number(page || 1));
  const query =
    options.query !== undefined ? String(options.query).trim() : state.historyQuery;
  const sort = options.sort || state.historySort || "newest";

  if (options.query !== undefined) {
    state.historyQuery = query;
  }
  if (options.sort) {
    state.historySort = HISTORY_SORTS.has(options.sort) ? options.sort : "newest";
  }

  state.busy.history = true;
  try {
    const logs = await fetchLogs(
      targetPage,
      state.historyFilter,
      query,
      state.historySort
    );
    updateHistory({
      ...logs,
      page: targetPage,
    });
    state.error = "";
    clearRetry();
    return logs;
  } catch (err) {
    setRequestError(err, {
      retryAction: () =>
        loadHistoryPage(targetPage, {
          query: state.historyQuery,
          sort: state.historySort,
        }),
      retryLabel: "Retry loading history",
    });
    throw err;
  } finally {
    state.busy.history = false;
  }
}

export async function changeHistoryFilter(filterValue) {
  state.historyFilter = filterValue;
  await loadHistoryPage(1);
}

export async function changeHistoryQuery(query) {
  state.historyQuery = String(query || "").trim();
  await loadHistoryPage(1);
}

export async function changeHistorySort(sortValue) {
  state.historySort = HISTORY_SORTS.has(sortValue) ? sortValue : "newest";
  await loadHistoryPage(1);
}

export async function loadSavedPage(page = 1, options = {}) {
  const targetPage = Math.max(1, Number(page || 1));
  const query = options.query !== undefined ? String(options.query).trim() : state.savedQuery;
  const sort = options.sort || state.savedSort || "newest";

  if (options.query !== undefined) {
    state.savedQuery = query;
  }
  if (options.sort) {
    state.savedSort = HISTORY_SORTS.has(options.sort) ? options.sort : "newest";
  }

  state.busy.saved = true;
  clearFormErrors("saved");
  try {
    const saved = await fetchSaved(targetPage, query, state.savedSort);
    updateSaved({
      ...saved,
      page: targetPage,
    });
    state.error = "";
    clearRetry();
    return saved;
  } catch (err) {
    setRequestError(err, {
      fieldScope: "saved",
      retryAction: () =>
        loadSavedPage(targetPage, {
          query: state.savedQuery,
          sort: state.savedSort,
        }),
      retryLabel: "Retry loading saved",
    });
    throw err;
  } finally {
    state.busy.saved = false;
  }
}

export async function changeSavedQuery(query) {
  state.savedQuery = String(query || "").trim();
  await loadSavedPage(1);
}

export async function changeSavedSort(sortValue) {
  state.savedSort = HISTORY_SORTS.has(sortValue) ? sortValue : "newest";
  await loadSavedPage(1);
}

export async function saveCurrentSuggestion() {
  if (!state.suggestion?.id) {
    return null;
  }

  state.busy.saved = true;
  clearFormErrors("saved");
  try {
    const result = await createSaved({ suggestion_id: state.suggestion.id });
    try {
      await loadSavedPage(1);
    } catch {
      // Saved refresh failure is already handled by loadSavedPage retry state.
    }
    if (!state.error) {
      setNotice("Saved for later.");
    }
    return result;
  } catch (err) {
    setRequestError(err, {
      fieldScope: "saved",
      retryAction: () => saveCurrentSuggestion(),
      retryLabel: "Retry saving",
    });
    throw err;
  } finally {
    state.busy.saved = false;
  }
}

export async function deleteSavedItem(item) {
  if (!item?.id) {
    return;
  }

  state.busy.saved = true;
  try {
    const deletedSnapshot = {
      suggestion_id: item.suggestion_id,
    };
    await destroySaved(item.id);
    const currentPage = Math.max(1, Number(state.savedPagination.page || 1));
    const targetPage = state.savedItems.length === 1 && currentPage > 1
      ? currentPage - 1
      : currentPage;

    try {
      await loadSavedPage(targetPage);
    } catch {
      // Saved refresh failure is already handled by loadSavedPage retry state.
    }

    if (!state.error) {
      setNotice("Saved item removed.", { preserveUndo: true });
      setUndo("Saved item removed.", async () => {
        await createSaved({ suggestion_id: deletedSnapshot.suggestion_id });
        await loadSavedPage(1, {
          query: state.savedQuery,
          sort: state.savedSort,
        });
        setNotice("Saved item restored.");
      });
    }
  } catch (err) {
    setRequestError(err, {
      retryAction: () => deleteSavedItem(item),
      retryLabel: "Retry removing saved item",
    });
    throw err;
  } finally {
    state.busy.saved = false;
  }
}

export function toggleCategoryGroup(categories) {
  const rawValues = Array.isArray(categories) ? categories : [categories];
  const allSelected = rawValues.every((category) =>
    state.constraints.excluded_categories.includes(category)
  );

  if (allSelected) {
    state.constraints.excluded_categories = state.constraints.excluded_categories.filter(
      (item) => !rawValues.includes(item)
    );
    return;
  }

  const nextValues = new Set(state.constraints.excluded_categories);
  rawValues.forEach((category) => nextValues.add(category));
  state.constraints.excluded_categories = [...nextValues];
}

export function resetGeneratedSuggestion() {
  if (state.suggestion && !state.suggestion.is_accepted) {
    state.suggestion = null;
  }

  if (Object.keys(state.formErrors.constraints).length) {
    clearFormErrors("constraints");
  }
}

export async function generateSuggestion() {
  state.busy.generate = true;
  clearFormErrors("constraints");
  try {
    const validationErrors = validateConstraints();
    if (Object.keys(validationErrors).length) {
      setInlineValidationErrors("constraints", validationErrors);
      throw createValidationError();
    }

    const result = await generateActivity({
      ...state.constraints,
      budget: String(getBudgetCap(state.constraints.budget_preference)),
    });
    state.suggestion = result;
    resetFeedback();
    clearFormErrors("completion");
    if (result.cooldown_relaxed && result.cooldown_message) {
      setNotice(result.cooldown_message);
    } else {
      setNotice("Generated a new suggestion.");
    }
    return result;
  } catch (err) {
    if (err?.isValidation) {
      throw err;
    }

    setRequestError(err, {
      fieldScope: "constraints",
      retryAction: () => generateSuggestion(),
      retryLabel: "Retry generating",
    });
    throw err;
  } finally {
    state.busy.generate = false;
  }
}

export async function rerollSuggestion() {
  if (!state.suggestion?.request_id) {
    return null;
  }

  state.busy.generate = true;
  try {
    const result = await rerollActivity(state.suggestion.request_id);
    state.suggestion = result;
    resetFeedback();
    clearFormErrors("completion");
    if (result.cooldown_relaxed && result.cooldown_message) {
      setNotice(result.cooldown_message);
    } else {
      setNotice("Generated another option.");
    }
    return result;
  } catch (err) {
    setRequestError(err, {
      retryAction: () => rerollSuggestion(),
      retryLabel: "Retry reroll",
    });
    throw err;
  } finally {
    state.busy.generate = false;
  }
}

export async function acceptCurrentSuggestion() {
  if (!state.suggestion?.id) {
    return null;
  }

  state.busy.accept = true;
  try {
    const result = await acceptSuggestion(state.suggestion.id);
    state.suggestion = result;
    try {
      await loadHistoryPage(1);
    } catch {
      // History refresh failure is already handled by loadHistoryPage retry state.
    }
    setNotice("Suggestion accepted. Head to Activity History to mark it as done or skipped.");
    return result;
  } catch (err) {
    setRequestError(err, {
      retryAction: () => acceptCurrentSuggestion(),
      retryLabel: "Retry accept",
    });
    throw err;
  } finally {
    state.busy.accept = false;
  }
}

export async function createActivityLog(status) {
  const suggestionId = state.suggestion?.id || state.pendingLog?.suggestion_id;

  if (!suggestionId) {
    return null;
  }

  state.busy.log = true;
  clearFormErrors("completion");
  try {
    const validationErrors = validateCompletion(status);
    if (Object.keys(validationErrors).length) {
      setInlineValidationErrors("completion", validationErrors);
      throw createValidationError();
    }

    const rawRating = String(state.completionForm.rating ?? "").trim();
    const payload = {
      suggestion_id: suggestionId,
      status,
      comment: state.completionForm.comment,
    };

    if (status === "COMPLETED" && rawRating) {
      payload.rating = Number(rawRating);
    }

    await createLog(payload);
    state.suggestion = null;
    resetFeedback();

    try {
      await loadHistoryPage(1);
    } catch {
      // History refresh failure is already handled by loadHistoryPage retry state.
    }

    if (!state.error) {
      setNotice(status === "COMPLETED" ? "Marked as done." : "Marked as skipped.");
    }
  } catch (err) {
    if (err?.isValidation) {
      throw err;
    }

    setRequestError(err, {
      fieldScope: "completion",
      retryAction: () => createActivityLog(status),
      retryLabel: "Retry saving log",
    });
    throw err;
  } finally {
    state.busy.log = false;
  }
}

export async function deleteHistoryLog(log) {
  if (!log?.id) {
    return;
  }

  state.busy.deleteLog = true;
  try {
    const deletedSnapshot = {
      suggestion_id: log.suggestion_id,
      status: log.status,
      rating: log.rating,
      comment: log.comment || "",
    };
    await destroyLog(log.id);

    if (state.pendingLog?.id === log.id) {
      state.pendingLog = null;
      clearFormErrors("completion");
      resetFeedback();
    }

    if (state.suggestion?.id === log.suggestion_id) {
      state.suggestion = null;
    }

    const currentPage = Math.max(1, Number(state.pagination.page || 1));
    const targetPage =
      log.status !== "ACCEPTED" && state.historyItems.length === 1 && currentPage > 1
        ? currentPage - 1
        : currentPage;

    try {
      await loadHistoryPage(targetPage);
    } catch {
      // History refresh failure is already handled by loadHistoryPage retry state.
    }

    if (!state.error) {
      setNotice("History item deleted.", { preserveUndo: true });
      setUndo("History item deleted.", async () => {
        await acceptSuggestion(deletedSnapshot.suggestion_id);
        if (deletedSnapshot.status !== "ACCEPTED") {
          const restorePayload = {
            suggestion_id: deletedSnapshot.suggestion_id,
            status: deletedSnapshot.status,
            comment: deletedSnapshot.comment,
          };
          if (
            deletedSnapshot.status === "COMPLETED"
            && Number.isInteger(Number(deletedSnapshot.rating))
          ) {
            restorePayload.rating = Number(deletedSnapshot.rating);
          }
          await createLog(restorePayload);
        }
        await loadHistoryPage(1, {
          query: state.historyQuery,
          sort: state.historySort,
        });
        setNotice("History item restored.");
      });
    }
  } catch (err) {
    setRequestError(err, {
      retryAction: () => deleteHistoryLog(log),
      retryLabel: "Retry deleting log",
    });
    throw err;
  } finally {
    state.busy.deleteLog = false;
  }
}

export function setUiPreference(key, value) {
  if (!Object.prototype.hasOwnProperty.call(state.uiPrefs, key)) {
    return;
  }

  state.uiPrefs = {
    ...state.uiPrefs,
    [key]: Boolean(value),
  };
  persistUiPrefs(state.uiPrefs);
  applyUiPrefsClasses(state.uiPrefs);
}

export function toggleUiPreference(key) {
  if (!Object.prototype.hasOwnProperty.call(state.uiPrefs, key)) {
    return;
  }

  setUiPreference(key, !state.uiPrefs[key]);
}

export async function retryLastRequest() {
  if (!state.retryAction) {
    return;
  }

  const action = state.retryAction;
  state.busy.retry = true;
  clearRetry();

  try {
    await action();
  } catch {
    // Error state is repopulated by the retried action.
  } finally {
    state.busy.retry = false;
  }
}

export async function undoLastDelete() {
  if (!undoAction) {
    return;
  }

  const action = undoAction;
  clearUndo();
  state.busy.retry = true;
  try {
    await action();
  } catch (err) {
    setRequestError(err, {
      retryAction: async () => {
        await action();
      },
      retryLabel: "Retry undo",
    });
    throw err;
  } finally {
    state.busy.retry = false;
  }
}

export async function loadAdminActivitiesList() {
  state.busy.admin = true;
  clearFormErrors("admin");
  try {
    const result = await fetchAdminActivities();
    state.error = "";
    clearRetry();
    return result;
  } catch (err) {
    setRequestError(err, {
      fieldScope: "admin",
      retryAction: () => loadAdminActivitiesList(),
      retryLabel: "Retry loading admin activities",
    });
    throw err;
  } finally {
    state.busy.admin = false;
  }
}

export async function loadAdminAuditLogs(page = 1) {
  const targetPage = Math.max(1, Number(page || 1));
  state.busy.admin = true;
  clearFormErrors("admin");
  try {
    const result = await fetchAdminAuditLogs(targetPage);
    updateAdminAudit({
      ...result,
      page: targetPage,
    });
    state.error = "";
    clearRetry();
    return result;
  } catch (err) {
    setRequestError(err, {
      fieldScope: "admin",
      retryAction: () => loadAdminAuditLogs(targetPage),
      retryLabel: "Retry loading audit logs",
    });
    throw err;
  } finally {
    state.busy.admin = false;
  }
}

export async function createAdminActivityEntry(payload) {
  state.busy.admin = true;
  clearFormErrors("admin");
  try {
    const result = await createAdminActivity(payload);
    setNotice("Activity created.");
    return result;
  } catch (err) {
    setRequestError(err, {
      fieldScope: "admin",
      retryAction: () => createAdminActivityEntry(payload),
      retryLabel: "Retry creating activity",
    });
    throw err;
  } finally {
    state.busy.admin = false;
  }
}

export async function updateAdminActivityEntry(activityId, payload) {
  state.busy.admin = true;
  clearFormErrors("admin");
  try {
    const result = await updateAdminActivity(activityId, payload);
    setNotice("Activity updated.");
    return result;
  } catch (err) {
    setRequestError(err, {
      fieldScope: "admin",
      retryAction: () => updateAdminActivityEntry(activityId, payload),
      retryLabel: "Retry updating activity",
    });
    throw err;
  } finally {
    state.busy.admin = false;
  }
}

export async function deleteAdminActivityEntry(activityId) {
  state.busy.admin = true;
  clearFormErrors("admin");
  try {
    await deleteAdminActivity(activityId);
    setNotice("Activity deleted.");
  } catch (err) {
    setRequestError(err, {
      fieldScope: "admin",
      retryAction: () => deleteAdminActivityEntry(activityId),
      retryLabel: "Retry deleting activity",
    });
    throw err;
  } finally {
    state.busy.admin = false;
  }
}

export async function importAdminActivitiesFromCsv(file) {
  state.busy.admin = true;
  clearFormErrors("admin");
  try {
    const result = await importAdminActivitiesCsv(file);
    setNotice(`CSV imported. Created ${result.created}, failed ${result.failed}.`);
    return result;
  } catch (err) {
    setRequestError(err, {
      fieldScope: "admin",
      retryAction: () => importAdminActivitiesFromCsv(file),
      retryLabel: "Retry CSV import",
    });
    throw err;
  } finally {
    state.busy.admin = false;
  }
}
