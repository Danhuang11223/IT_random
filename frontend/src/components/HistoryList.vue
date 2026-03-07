<script setup>
import { computed, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import { getCategoryOption } from "../categoryOptions";
import {
  changeHistoryFilter,
  changeHistoryQuery,
  changeHistorySort,
  createActivityLog,
  deleteHistoryLog,
  historyPageNumbers,
  loadHistoryPage,
  state,
} from "../state";

const hasPagination = computed(() => state.pagination.total_pages > 1);
const pendingSuggestion = computed(() => state.pendingLog);
const actionButtonsDisabled = computed(
  () => state.busy.history || state.busy.log || state.busy.deleteLog
);
const localQuery = ref(state.historyQuery);
const ratingOptions = [1, 2, 3, 4, 5];
const filters = [
  { label: "All", value: "ALL" },
  { label: "Completed", value: "COMPLETED" },
  { label: "Skipped", value: "SKIPPED" },
];
const sortOptions = [
  { value: "newest", label: "Newest first" },
  { value: "oldest", label: "Oldest first" },
  { value: "title", label: "Title A-Z" },
];

watch(
  () => state.historyQuery,
  (value) => {
    localQuery.value = value;
  }
);

async function handlePageChange(page) {
  try {
    await loadHistoryPage(page);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleFilterChange(filterValue) {
  if (state.busy.history || state.historyFilter === filterValue) {
    return;
  }

  try {
    await changeHistoryFilter(filterValue);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleComplete() {
  try {
    await createActivityLog("COMPLETED");
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleSkip() {
  try {
    await createActivityLog("SKIPPED");
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleDelete(log) {
  try {
    await deleteHistoryLog(log);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleQuerySubmit() {
  try {
    await changeHistoryQuery(localQuery.value);
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleSortChange(event) {
  try {
    await changeHistorySort(event.target.value);
  } catch {
    // Error state is handled in shared state.
  }
}

function normalizeMoney(value) {
  return Math.round(Number(value || 0));
}

function formatBudgetRange(activity) {
  const minBudget = normalizeMoney(activity?.min_budget);
  const maxBudget = normalizeMoney(activity?.max_budget);

  if (minBudget === 0 && maxBudget === 0) {
    return "Free";
  }
  if (minBudget === maxBudget) {
    return `£${maxBudget}`;
  }
  return `£${minBudget} - £${maxBudget}`;
}

function setRating(value) {
  state.completionForm.rating = String(value);
}

function clearRating() {
  state.completionForm.rating = "";
}

function isRatingActive(value) {
  return Number(state.completionForm.rating || 0) === value;
}

function formatDateOnly(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value).split("T")[0] || "-";
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}/${month}/${day}`;
}
</script>

<template>
  <section class="panel history-panel wide-panel history-board-card">
    <div class="panel-heading">
      <h2>Activity History</h2>
      <p>What you've tried so far. Kept it — or skipped it.</p>
    </div>

    <div v-if="pendingSuggestion" class="pending-log-card">
      <div class="history-head">
        <strong>{{ pendingSuggestion.activity.title }}</strong>
        <span class="status-pill pending">Pending</span>
      </div>
      <div class="record-tag-row">
        <span class="record-tag">{{ getCategoryOption(pendingSuggestion.activity.category).label }}</span>
        <span class="record-tag">
          ⏱ {{ pendingSuggestion.activity.min_time_minutes }}-{{ pendingSuggestion.activity.max_time_minutes }} min
        </span>
        <span class="record-tag">💰 {{ formatBudgetRange(pendingSuggestion.activity) }}</span>
        <span class="record-tag">📅 {{ formatDateOnly(pendingSuggestion.created_at) }}</span>
      </div>
      <p class="history-meta">Accepted and waiting to be logged.</p>
      <p class="pending-card-copy">
        {{ pendingSuggestion.activity.description }}
      </p>

      <div class="stack compact">
        <p v-if="state.formErrors.completion._form" class="form-inline-error">
          {{ state.formErrors.completion._form }}
        </p>

        <label class="field">
          <span>Your rating (optional)</span>
          <div class="rating-stars">
            <button
              v-for="rating in ratingOptions"
              :key="rating"
              type="button"
              class="star-chip"
              :class="{ active: isRatingActive(rating) }"
              :aria-pressed="isRatingActive(rating)"
              @click="setRating(rating)"
            >
              {{ "★".repeat(rating) }}
            </button>
            <button type="button" class="ghost-button small-button" @click="clearRating">
              Clear
            </button>
          </div>
          <small v-if="state.formErrors.completion.rating" class="field-error">
            {{ state.formErrors.completion.rating }}
          </small>
        </label>

        <label class="field">
          <span>Notes (optional)</span>
          <textarea
            v-model="state.completionForm.comment"
            rows="2"
            class="notes-compact"
            :class="{ 'invalid-input': state.formErrors.completion.comment }"
          />
          <small v-if="state.formErrors.completion.comment" class="field-error">
            {{ state.formErrors.completion.comment }}
          </small>
        </label>

        <div class="button-row">
          <button
            class="primary-button"
            :disabled="actionButtonsDisabled"
            @click="handleComplete"
          >
            {{ state.busy.log ? "Saving..." : "Mark as done" }}
          </button>

          <button
            class="ghost-button"
            :disabled="actionButtonsDisabled"
            @click="handleSkip"
          >
            Skip
          </button>

          <button
            class="ghost-button small-button"
            :disabled="actionButtonsDisabled"
            @click="handleDelete(pendingSuggestion)"
          >
            {{ state.busy.deleteLog ? "Deleting..." : "Delete" }}
          </button>
        </div>
      </div>
    </div>

    <div class="history-toolbar stack-on-mobile">
      <div class="filter-group">
        <button
          v-for="filter in filters"
          :key="filter.value"
          type="button"
          class="filter-chip"
          :class="{ active: state.historyFilter === filter.value }"
          :disabled="state.busy.history"
          @click="handleFilterChange(filter.value)"
        >
          {{ filter.label }}
        </button>
      </div>

      <form class="search-form" @submit.prevent="handleQuerySubmit">
        <label for="history-search" class="sr-only">Search history</label>
        <input
          id="history-search"
          v-model="localQuery"
          type="search"
          placeholder="Search title or notes"
        />
        <button class="ghost-button small-button" :disabled="state.busy.history">
          Search
        </button>
      </form>

      <label class="sort-control">
        <span>Sort</span>
        <select
          :value="state.historySort"
          :disabled="state.busy.history"
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

    <div
      v-if="state.busy.dashboard && !state.historyItems.length && !pendingSuggestion"
      class="empty-state"
    >
      <p>Loading history...</p>
    </div>

    <ul v-else-if="state.historyItems.length" class="history-list">
      <li v-for="item in state.historyItems" :key="item.id" class="history-item">
        <div class="history-head">
          <strong>{{ item.activity.title }}</strong>
          <div class="history-actions">
            <span class="status-pill" :class="item.status.toLowerCase()">
              {{ item.status === "COMPLETED" ? "Done" : "Skipped" }}
            </span>
            <button
              class="ghost-button small-button"
              :disabled="state.busy.deleteLog"
              @click="handleDelete(item)"
            >
              {{ state.busy.deleteLog ? "Deleting..." : "Delete" }}
            </button>
          </div>
        </div>
        <div class="record-tag-row">
          <span class="record-tag">{{ getCategoryOption(item.activity.category).label }}</span>
          <span class="record-tag">
            ⏱ {{ item.activity.min_time_minutes }}-{{ item.activity.max_time_minutes }} min
          </span>
          <span class="record-tag">💰 {{ formatBudgetRange(item.activity) }}</span>
          <span class="record-tag">⭐ {{ item.rating ?? "-" }}</span>
          <span class="record-tag">📅 {{ formatDateOnly(item.updated_at || item.created_at) }}</span>
        </div>
        <p v-if="item.comment" class="history-comment">{{ item.comment }}</p>
      </li>
    </ul>

    <div v-if="state.historyItems.length" class="history-pagination">
      <button
        class="ghost-button"
        :disabled="state.busy.history || state.pagination.page <= 1"
        @click="handlePageChange(state.pagination.page - 1)"
      >
        Previous
      </button>

      <div class="page-indicator">
        <strong>Page {{ state.pagination.page }} / {{ state.pagination.total_pages }}</strong>
        <span v-if="state.busy.history" class="subtle-hint">Switching pages...</span>
        <span v-else-if="hasPagination">{{ state.pagination.count }} total records</span>
      </div>

      <div v-if="hasPagination" class="page-number-group">
        <template v-for="item in historyPageNumbers" :key="item.key">
          <button
            v-if="item.type === 'page'"
            type="button"
            class="page-number-button"
            :class="{ active: state.pagination.page === item.value }"
            :disabled="state.busy.history"
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
          state.busy.history || state.pagination.page >= state.pagination.total_pages
        "
        @click="handlePageChange(state.pagination.page + 1)"
      >
        Next
      </button>
    </div>

    <div v-else class="empty-state playful-empty">
      <div class="empty-illustration" aria-hidden="true">🗂️</div>
      <p class="empty-title">
        {{
          pendingSuggestion
            ? "No history yet. Finish the current suggestion first."
            : "Nothing here yet."
        }}
      </p>
      <p class="empty-subtitle">
        {{
          pendingSuggestion
            ? "Mark it as done or skipped, and it will show up here."
            : "Start with ✨ Surprise me and build your activity trail."
        }}
      </p>
      <RouterLink v-if="!pendingSuggestion" class="primary-link empty-cta" to="/dashboard">
        Go to Generator
      </RouterLink>
    </div>

  </section>
</template>
