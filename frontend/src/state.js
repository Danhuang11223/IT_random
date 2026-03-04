import { computed, reactive } from "vue";

import {
  acceptSuggestion,
  clearSession,
  createLog,
  deleteLog as destroyLog,
  fetchLogs,
  fetchMetadata,
  generateActivity,
  getStoredToken,
  getStoredUser,
  login,
  register,
  rerollActivity,
} from "./api";

const initialConstraints = () => ({
  time_minutes: "",
  budget: "",
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
});

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
  pagination: {
    count: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
    next: null,
    previous: null,
  },
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
    retry: false,
  },
});

export const isLoggedIn = computed(() => Boolean(state.sessionToken));
export const canReroll = computed(() => Boolean(state.suggestion?.request_id));
export const hasPendingAcceptedSuggestion = computed(() =>
  Boolean(state.pendingLog || state.suggestion?.is_accepted)
);
export const historyPageNumbers = computed(() => {
  const totalPages = Math.max(1, Number(state.pagination.total_pages || 1));
  const currentPage = Math.min(
    totalPages,
    Math.max(1, Number(state.pagination.page || 1))
  );
  const items = [];

  const pushPage = (page) => {
    items.push({
      type: "page",
      value: page,
      key: `page-${page}`,
    });
  };

  const pushEllipsis = (position) => {
    items.push({
      type: "ellipsis",
      value: "...",
      key: `ellipsis-${position}`,
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
});

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

  return "请求失败，请检查后端服务是否已启动。";
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
    errors.username = "请输入用户名。";
  }

  if (!String(credentials.password || "").trim()) {
    errors.password = "请输入密码。";
  }

  return errors;
}

function validateRegisterPayload(payload) {
  const errors = {};
  const username = String(payload.username || "").trim();
  const email = String(payload.email || "").trim();
  const password = String(payload.password || "");

  if (!username) {
    errors.username = "请输入用户名。";
  } else if (username.length < 3) {
    errors.username = "用户名至少需要 3 个字符。";
  }

  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = "请输入有效的邮箱地址。";
  }

  if (!password.trim()) {
    errors.password = "请输入密码。";
  } else if (password.length < 8) {
    errors.password = "密码至少需要 8 个字符。";
  } else if (password.length > 128) {
    errors.password = "密码长度不能超过 128 个字符。";
  }

  return errors;
}

function validateConstraints() {
  const errors = {};
  const rawTimeValue = String(state.constraints.time_minutes ?? "").trim();
  const rawBudgetValue = String(state.constraints.budget ?? "").trim();
  const timeValue = Number(rawTimeValue);
  const budgetValue = Number(rawBudgetValue);

  if (!rawTimeValue) {
    errors.time_minutes = "请输入可用时间。";
  } else if (!Number.isInteger(timeValue)) {
    errors.time_minutes = "请输入整数分钟数。";
  } else if (timeValue < 5 || timeValue > 1440) {
    errors.time_minutes = "时间范围需要在 5 到 1440 分钟之间。";
  } else if (timeValue % 5 !== 0) {
    errors.time_minutes = "时间请按 5 分钟为单位填写。";
  }

  if (!rawBudgetValue) {
    errors.budget = "请输入预算。";
  } else if (Number.isNaN(budgetValue)) {
    errors.budget = "请输入有效预算。";
  } else if (!Number.isInteger(budgetValue)) {
    errors.budget = "预算请填写整数。";
  } else if (budgetValue < 0) {
    errors.budget = "预算不能小于 0。";
  } else if (budgetValue > 999999) {
    errors.budget = "预算超出允许范围。";
  }

  if (!String(state.constraints.mood || "").trim()) {
    errors.mood = "请选择当前心情。";
  }

  if (!String(state.constraints.social_preference || "").trim()) {
    errors.social_preference = "请选择社交偏好。";
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
      errors.rating = "评分必须是整数。";
    } else if (ratingValue < 1 || ratingValue > 5) {
      errors.rating = "评分范围需要在 1 到 5 之间。";
    }
  }

  if (commentValue.length > 500) {
    errors.comment = "备注最多 500 个字符。";
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
  state.pagination = {
    count: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
    next: null,
    previous: null,
  };
  clearFormErrors();
  clearRetry();
  resetFeedback();
}

export function setNotice(text) {
  state.message = text;
  state.error = "";
  clearRetry();
}

function setRetry(retryAction, retryLabel) {
  state.retryAction = retryAction || null;
  state.retryLabel = retryAction ? retryLabel || "重试" : "";
}

function setRequestError(err, options = {}) {
  const { fieldScope = null, retryAction = null, retryLabel = "重试" } = options;
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
      setNotice(`已登录：${result.user.username}`);
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
      retryLabel: "重试登录",
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
      setNotice(`注册成功：${result.user.username}`);
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
      retryLabel: "重试注册",
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
  setNotice("已退出登录。");
}

export async function loadDashboardData(options = {}) {
  if (state.dashboardReady && !options.force) {
    return;
  }

  state.busy.dashboard = true;
  try {
    const targetPage = Math.max(1, Number(options.page || 1));
    const [meta, logs] = await Promise.all([
      fetchMetadata(),
      fetchLogs(targetPage, state.historyFilter),
    ]);
    state.metadata = {
      categories: meta.categories || [],
      moods: meta.moods || [],
      social_preferences: meta.social_preferences || [],
    };
    syncDefaults();
    updateHistory({
      ...logs,
      page: targetPage,
    });
    state.dashboardReady = true;
    state.error = "";
    clearRetry();
  } catch (err) {
    state.dashboardReady = false;
    setRequestError(err, {
      retryAction: () => loadDashboardData({ force: true }),
      retryLabel: "重试加载控制台",
    });
    throw err;
  } finally {
    state.busy.dashboard = false;
  }
}

export async function loadHistoryPage(page = 1) {
  const targetPage = Math.max(1, Number(page || 1));

  state.busy.history = true;
  try {
    const logs = await fetchLogs(targetPage, state.historyFilter);
    updateHistory({
      ...logs,
      page: targetPage,
    });
    state.error = "";
    clearRetry();
    return logs;
  } catch (err) {
    setRequestError(err, {
      retryAction: () => loadHistoryPage(targetPage),
      retryLabel: "重试加载历史记录",
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
      budget: String(state.constraints.budget),
    });
    state.suggestion = result;
    resetFeedback();
    clearFormErrors("completion");
    setNotice("已生成一个随机事件。");
    return result;
  } catch (err) {
    if (err?.isValidation) {
      throw err;
    }

    setRequestError(err, {
      fieldScope: "constraints",
      retryAction: () => generateSuggestion(),
      retryLabel: "重试生成",
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
    setNotice("已为当前请求重抽一个结果。");
    return result;
  } catch (err) {
    setRequestError(err, {
      retryAction: () => rerollSuggestion(),
      retryLabel: "重试重抽",
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
    setNotice("已接受当前建议。请前往历史记录标记完成或跳过。");
    return result;
  } catch (err) {
    setRequestError(err, {
      retryAction: () => acceptCurrentSuggestion(),
      retryLabel: "重试接受",
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
      setNotice(status === "COMPLETED" ? "已记录完成。" : "已记录跳过。");
    }
  } catch (err) {
    if (err?.isValidation) {
      throw err;
    }

    setRequestError(err, {
      fieldScope: "completion",
      retryAction: () => createActivityLog(status),
      retryLabel: "重试提交记录",
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
      setNotice("已删除历史记录。");
    }
  } catch (err) {
    setRequestError(err, {
      retryAction: () => deleteHistoryLog(log),
      retryLabel: "重试删除记录",
    });
    throw err;
  } finally {
    state.busy.deleteLog = false;
  }
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
