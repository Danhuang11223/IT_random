<script setup>
import { onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import HistoryList from "../components/HistoryList.vue";
import { loadDashboardData, loadHistoryPage, state } from "../state";

const route = useRoute();
const router = useRouter();
const VALID_HISTORY_FILTERS = new Set(["ALL", "COMPLETED", "SKIPPED"]);

function normalizeHistoryQuery(query) {
  const rawStatus = Array.isArray(query.status) ? query.status[0] : query.status;
  const normalizedStatus = String(rawStatus || "ALL").toUpperCase();
  const status = VALID_HISTORY_FILTERS.has(normalizedStatus)
    ? normalizedStatus
    : "ALL";

  const rawPage = Array.isArray(query.page) ? query.page[0] : query.page;
  const parsedPage = Number.parseInt(String(rawPage || "1"), 10);
  const page = Number.isInteger(parsedPage) && parsedPage > 0 ? parsedPage : 1;

  return { page, status };
}

function buildHistoryQuery(status, page) {
  const query = {};

  if (status && status !== "ALL") {
    query.status = status;
  }

  if (page > 1) {
    query.page = String(page);
  }

  return query;
}

function getTrackedRouteQuery() {
  const query = {};

  if (typeof route.query.status === "string") {
    query.status = route.query.status;
  }

  if (typeof route.query.page === "string") {
    query.page = route.query.page;
  }

  return query;
}

function isSameQuery(left, right) {
  const leftKeys = Object.keys(left);
  const rightKeys = Object.keys(right);

  if (leftKeys.length !== rightKeys.length) {
    return false;
  }

  return leftKeys.every((key) => left[key] === right[key]);
}

async function syncRouteFromState() {
  const desiredQuery = buildHistoryQuery(
    state.historyFilter,
    state.pagination.page || 1
  );

  if (isSameQuery(getTrackedRouteQuery(), desiredQuery)) {
    return;
  }

  await router.replace({ name: "history", query: desiredQuery });
}

async function applyHistoryQuery(force = false) {
  const { page, status } = normalizeHistoryQuery(route.query);
  const shouldReload =
    force ||
    !state.dashboardReady ||
    state.historyFilter !== status ||
    state.pagination.page !== page;

  if (!shouldReload) {
    await syncRouteFromState();
    return;
  }

  state.historyFilter = status;

  try {
    if (!state.dashboardReady || force) {
      await loadDashboardData({ force: true, page });
    } else {
      await loadHistoryPage(page);
    }
  } catch {
    return;
  }

  await syncRouteFromState();
}

onMounted(async () => {
  try {
    await applyHistoryQuery(!state.dashboardReady);
  } catch {
    // Error banner is handled in global state.
  }
});

watch(
  () => [route.query.page, route.query.status],
  async () => {
    if (state.busy.dashboard || state.busy.history) {
      return;
    }

    try {
      await applyHistoryQuery();
    } catch {
      // Error banner is handled in global state.
    }
  }
);

watch(
  () => [
    state.historyFilter,
    state.pagination.page,
    state.busy.dashboard,
    state.busy.history,
  ],
  async ([, , busyDashboard, busyHistory]) => {
    if (busyDashboard || busyHistory) {
      return;
    }

    try {
      await syncRouteFromState();
    } catch {
      // Ignore navigation duplication during query sync.
    }
  }
);
</script>

<template>
  <main class="single-column history-flow">
    <HistoryList />
  </main>
</template>
