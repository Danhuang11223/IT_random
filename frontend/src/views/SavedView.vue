<script setup>
import { onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import SavedList from "../components/SavedList.vue";
import { loadDashboardData, loadSavedPage, state } from "../state";

const route = useRoute();
const router = useRouter();
const VALID_SORTS = new Set(["newest", "oldest", "title"]);

function normalizeSavedQuery(query) {
  const rawPage = Array.isArray(query.page) ? query.page[0] : query.page;
  const parsedPage = Number.parseInt(String(rawPage || "1"), 10);
  const page = Number.isInteger(parsedPage) && parsedPage > 0 ? parsedPage : 1;

  const rawQuery = Array.isArray(query.q) ? query.q[0] : query.q;
  const q = String(rawQuery || "").trim();

  const rawSort = Array.isArray(query.sort) ? query.sort[0] : query.sort;
  const normalizedSort = String(rawSort || "newest").toLowerCase();
  const sort = VALID_SORTS.has(normalizedSort) ? normalizedSort : "newest";

  return { page, q, sort };
}

function buildSavedQuery(page, q, sort) {
  const query = {};

  if (page > 1) {
    query.page = String(page);
  }

  if (q) {
    query.q = q;
  }

  if (sort && sort !== "newest") {
    query.sort = sort;
  }

  return query;
}

function getTrackedRouteQuery() {
  const query = {};

  if (typeof route.query.page === "string") {
    query.page = route.query.page;
  }

  if (typeof route.query.q === "string" && route.query.q.trim()) {
    query.q = route.query.q.trim();
  }

  if (typeof route.query.sort === "string" && route.query.sort !== "newest") {
    query.sort = route.query.sort;
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
  const desiredQuery = buildSavedQuery(
    state.savedPagination.page || 1,
    state.savedQuery,
    state.savedSort
  );

  if (isSameQuery(getTrackedRouteQuery(), desiredQuery)) {
    return;
  }

  await router.replace({ name: "saved", query: desiredQuery });
}

async function applySavedQuery(force = false) {
  const { page, q, sort } = normalizeSavedQuery(route.query);
  const shouldReload =
    force ||
    !state.dashboardReady ||
    state.savedPagination.page !== page ||
    state.savedQuery !== q ||
    state.savedSort !== sort;

  if (!shouldReload) {
    await syncRouteFromState();
    return;
  }

  state.savedQuery = q;
  state.savedSort = sort;

  try {
    if (!state.dashboardReady || force) {
      await loadDashboardData({ force: true, savedPage: page });
    } else {
      await loadSavedPage(page, { query: q, sort });
    }
  } catch {
    return;
  }

  await syncRouteFromState();
}

onMounted(async () => {
  try {
    await applySavedQuery(!state.dashboardReady);
  } catch {
    // Error banner is handled in shared state.
  }
});

watch(
  () => [route.query.page, route.query.q, route.query.sort],
  async () => {
    if (state.busy.dashboard || state.busy.saved) {
      return;
    }

    try {
      await applySavedQuery();
    } catch {
      // Error banner is handled in shared state.
    }
  }
);

watch(
  () => [
    state.savedQuery,
    state.savedSort,
    state.savedPagination.page,
    state.busy.dashboard,
    state.busy.saved,
  ],
  async ([, , , busyDashboard, busySaved]) => {
    if (busyDashboard || busySaved) {
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
    <SavedList />
  </main>
</template>
