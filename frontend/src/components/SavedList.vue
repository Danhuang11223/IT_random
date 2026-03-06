<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { getCategoryOption } from "../categoryOptions";
import CalendarModal from "./CalendarModal.vue";
import {
  changeSavedQuery,
  changeSavedSort,
  deleteSavedItem,
  loadSavedPage,
  savedPageNumbers,
  setNotice,
  state,
} from "../state";

const router = useRouter();
const localQuery = ref(state.savedQuery);
const selectedCalendarActivity = ref(null);
const calendarOpen = ref(false);
const sortOptions = [
  { value: "newest", label: "Newest first" },
  { value: "oldest", label: "Oldest first" },
  { value: "title", label: "Title A-Z" },
];

watch(
  () => state.savedQuery,
  (value) => {
    localQuery.value = value;
  }
);

const hasPagination = computed(() => state.savedPagination.total_pages > 1);

function openCalendar(activity) {
  selectedCalendarActivity.value = activity;
  calendarOpen.value = true;
}

function formatSavedDate(timestamp) {
  if (!timestamp) {
    return "-";
  }

  try {
    return new Intl.DateTimeFormat("en-GB", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(timestamp));
  } catch {
    return timestamp;
  }
}

function normalizeMoney(value) {
  return Math.round(Number(value || 0));
}

function formatBudgetRange(activity) {
  const minBudget = normalizeMoney(activity.min_budget);
  const maxBudget = normalizeMoney(activity.max_budget);

  if (minBudget === 0 && maxBudget === 0) {
    return "Free";
  }

  if (minBudget === maxBudget) {
    return `£${maxBudget}`;
  }

  return `£${minBudget} - £${maxBudget}`;
}

async function handleQuerySubmit() {
  try {
    await changeSavedQuery(localQuery.value);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleSortChange(event) {
  try {
    await changeSavedSort(event.target.value);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handlePageChange(page) {
  try {
    await loadSavedPage(page);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleDelete(item) {
  try {
    await deleteSavedItem(item);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleUseThisIdea(item) {
  state.suggestion = {
    id: item.suggestion_id,
    request_id: item.request_id,
    rank_no: 1,
    is_accepted: item.is_accepted,
    created_at: item.created_at,
    activity: item.activity,
    fallback_applied: false,
    fallback_message: "",
    cooldown_relaxed: false,
    cooldown_message: "",
  };
  setNotice("Loaded saved suggestion into Generator.");
  await router.push("/dashboard");
}
</script>

<template>
  <section class="panel history-panel wide-panel history-board-card">
    <div class="panel-heading">
      <h2>Saved for Later</h2>
      <p>Ideas you kept without accepting yet. Revisit, schedule, or remove them.</p>
    </div>

    <div class="history-toolbar stack-on-mobile">
      <form class="search-form" @submit.prevent="handleQuerySubmit">
        <label for="saved-search" class="sr-only">Search saved ideas</label>
        <input
          id="saved-search"
          v-model="localQuery"
          type="search"
          placeholder="Search title or description"
        />
        <button class="ghost-button small-button" :disabled="state.busy.saved">
          Search
        </button>
      </form>

      <label class="sort-control">
        <span>Sort</span>
        <select
          :value="state.savedSort"
          :disabled="state.busy.saved"
          @change="handleSortChange"
        >
          <option
            v-for="option in sortOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </label>
    </div>

    <div v-if="state.busy.saved && !state.savedItems.length" class="empty-state">
      <p>Loading saved items...</p>
    </div>

    <ul v-else-if="state.savedItems.length" class="history-list">
      <li v-for="item in state.savedItems" :key="item.id" class="history-item">
        <div class="history-head">
          <strong>{{ item.activity.title }}</strong>
          <div class="history-actions">
            <span class="status-pill" :class="item.is_accepted ? 'completed' : 'pending'">
              {{ item.is_accepted ? "Accepted" : "Saved" }}
            </span>
          </div>
        </div>

        <p class="history-meta">
          {{ getCategoryOption(item.activity.category).label }} · {{ formatSavedDate(item.created_at) }}
        </p>
        <p class="history-comment">{{ item.activity.description }}</p>
        <p class="history-meta">
          {{ item.activity.min_time_minutes }} - {{ item.activity.max_time_minutes }} min ·
          {{ formatBudgetRange(item.activity) }}
        </p>

        <div class="button-row">
          <button class="ghost-button small-button" @click="openCalendar(item.activity)">
            Add to Calendar
          </button>
          <button class="ghost-button small-button" @click="handleUseThisIdea(item)">
            Use this idea
          </button>
          <button
            class="ghost-button small-button"
            :disabled="state.busy.saved"
            @click="handleDelete(item)"
          >
            {{ state.busy.saved ? "Removing..." : "Remove" }}
          </button>
        </div>
      </li>
    </ul>

    <div v-else class="empty-state playful-empty">
      <div class="empty-illustration" aria-hidden="true">📌</div>
      <p class="empty-title">Nothing saved yet.</p>
      <p class="empty-subtitle">Save activities from the Generator<br>and they will appear here.</p>
    </div>

    <div v-if="state.savedItems.length" class="history-pagination">
      <button
        class="ghost-button"
        :disabled="state.busy.saved || state.savedPagination.page <= 1"
        @click="handlePageChange(state.savedPagination.page - 1)"
      >
        Previous
      </button>

      <div class="page-indicator">
        <strong>Page {{ state.savedPagination.page }} / {{ state.savedPagination.total_pages }}</strong>
        <span v-if="state.busy.saved" class="subtle-hint">Switching pages...</span>
        <span v-else-if="hasPagination">{{ state.savedPagination.count }} total saved</span>
      </div>

      <div v-if="hasPagination" class="page-number-group">
        <template v-for="item in savedPageNumbers" :key="item.key">
          <button
            v-if="item.type === 'page'"
            type="button"
            class="page-number-button"
            :class="{ active: state.savedPagination.page === item.value }"
            :disabled="state.busy.saved"
            @click="handlePageChange(item.value)"
          >
            {{ item.value }}
          </button>
          <span v-else class="page-ellipsis" aria-hidden="true">…</span>
        </template>
      </div>

      <button
        class="ghost-button"
        :disabled="
          state.busy.saved || state.savedPagination.page >= state.savedPagination.total_pages
        "
        @click="handlePageChange(state.savedPagination.page + 1)"
      >
        Next
      </button>
    </div>

    <CalendarModal
      v-model="calendarOpen"
      :activity="selectedCalendarActivity"
    />
  </section>
</template>
