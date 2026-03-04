<script setup>
import { computed } from "vue";

import { getCategoryOption } from "../categoryOptions";
import {
  changeHistoryFilter,
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
const filters = [
  { label: "All", value: "ALL" },
  { label: "Completed", value: "COMPLETED" },
  { label: "Skipped", value: "SKIPPED" },
];

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
</script>

<template>
  <section class="panel history-panel wide-panel">
    <div class="panel-heading">
      <h2>Activity History</h2>
      <p>What you've tried so far. Kept it — or skipped it.</p>
    </div>

    <div v-if="pendingSuggestion" class="pending-log-card">
      <div class="history-head">
        <strong>{{ pendingSuggestion.activity.title }}</strong>
        <span class="status-pill pending">Pending</span>
      </div>
      <p class="history-meta">
        {{ getCategoryOption(pendingSuggestion.activity.category).label }} · Accepted · waiting to be logged
      </p>
      <p class="pending-card-copy">
        {{ pendingSuggestion.activity.description }}
      </p>

      <div class="stack compact">
        <p v-if="state.formErrors.completion._form" class="form-inline-error">
          {{ state.formErrors.completion._form }}
        </p>

        <label class="field">
          <span>Rating (optional, saved only when marked done)</span>
          <input
            v-model="state.completionForm.rating"
            type="number"
            min="1"
            max="5"
            :class="{ 'invalid-input': state.formErrors.completion.rating }"
          />
          <small v-if="state.formErrors.completion.rating" class="field-error">
            {{ state.formErrors.completion.rating }}
          </small>
        </label>

        <label class="field">
          <span>Notes (optional)</span>
          <textarea
            v-model="state.completionForm.comment"
            rows="3"
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
            Mark as skipped
          </button>

          <button
            class="ghost-button small-button"
            :disabled="actionButtonsDisabled"
            @click="handleDelete(pendingSuggestion)"
          >
            {{ state.busy.deleteLog ? "Deleting..." : "Delete pending" }}
          </button>
        </div>
      </div>
    </div>

    <div class="history-toolbar">
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
        <p class="history-meta">
          {{ getCategoryOption(item.activity.category).label }} · Rating {{ item.rating ?? "-" }}
        </p>
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

    <div v-else class="empty-state">
      <p>
        {{
          pendingSuggestion
            ? "Nothing here yet. Finish the current item first."
            : "Nothing here yet. Start with ✨ Generate Activity."
        }}
      </p>
    </div>
  </section>
</template>
