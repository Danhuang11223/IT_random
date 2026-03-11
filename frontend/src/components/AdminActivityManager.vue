<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import {
  createAdminActivityEntry,
  deleteAdminActivityEntry,
  importAdminActivitiesFromCsv,
  loadAdminActivitiesList,
  loadAdminAuditLogs,
  state,
  updateAdminActivityEntry,
} from "../state";

const activities = ref([]);
const importSummary = ref(null);
const auditLogs = ref([]);
const editingId = ref(null);
const csvFile = ref(null);
const adminPagination = ref({
  count: 0,
  page: 1,
  total_pages: 1,
  next: null,
  previous: null,
});
const createForm = reactive({
  title: "",
  description: "",
  category: "INDOOR",
  min_time_minutes: 15,
  max_time_minutes: 45,
  min_budget: 0,
  max_budget: 20,
  mood_tags: "low,medium",
  social_type: "EITHER",
  is_outdoor: false,
  is_active: true,
});
const editForm = reactive({
  title: "",
  description: "",
  category: "",
  min_time_minutes: 0,
  max_time_minutes: 0,
  min_budget: 0,
  max_budget: 0,
  mood_tags: "",
  social_type: "EITHER",
  is_outdoor: false,
  is_active: true,
});
const socialOptions = ["SOLO", "FRIENDS", "EITHER"];
const totalCount = computed(() =>
  Number(adminPagination.value.count || activities.value.length)
);
const hasPagination = computed(
  () => Number(adminPagination.value.total_pages || 1) > 1
);

function normalizeTags(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function parseActivityPayload(form) {
  return {
    title: String(form.title || "").trim(),
    description: String(form.description || "").trim(),
    category: String(form.category || "").trim().toUpperCase(),
    min_time_minutes: Number(form.min_time_minutes),
    max_time_minutes: Number(form.max_time_minutes),
    min_budget: Number(form.min_budget),
    max_budget: Number(form.max_budget),
    mood_tags: normalizeTags(form.mood_tags),
    social_type: String(form.social_type || "EITHER").trim().toUpperCase(),
    is_outdoor: Boolean(form.is_outdoor),
    is_active: Boolean(form.is_active),
  };
}

function hydrateEditForm(item) {
  editForm.title = item.title;
  editForm.description = item.description || "";
  editForm.category = item.category || "";
  editForm.min_time_minutes = item.min_time_minutes;
  editForm.max_time_minutes = item.max_time_minutes;
  editForm.min_budget = Number(item.min_budget || 0);
  editForm.max_budget = Number(item.max_budget || 0);
  editForm.mood_tags = Array.isArray(item.mood_tags) ? item.mood_tags.join(",") : "";
  editForm.social_type = item.social_type || "EITHER";
  editForm.is_outdoor = Boolean(item.is_outdoor);
  editForm.is_active = Boolean(item.is_active);
}

async function refreshList(page = 1) {
  const targetPage = Math.max(1, Number(page || 1));
  try {
    const result = await loadAdminActivitiesList(targetPage);
    if (Array.isArray(result?.results)) {
      activities.value = result.results;
      adminPagination.value = {
        count: Number(result.count || 0),
        page: targetPage,
        total_pages: Math.max(
          1,
          Math.ceil(Number(result.count || 0) / 4)
        ),
        next: result.next || null,
        previous: result.previous || null,
      };
      if (
        !activities.value.length
        && adminPagination.value.page > 1
        && adminPagination.value.count > 0
      ) {
        await refreshList(adminPagination.value.page - 1);
      }
      return;
    }

    activities.value = Array.isArray(result) ? result : [];
    adminPagination.value = {
      count: activities.value.length,
      page: 1,
      total_pages: 1,
      next: null,
      previous: null,
    };
  } catch (error) {
    if (error?.response?.status === 404 && targetPage > 1) {
      await refreshList(targetPage - 1);
      return;
    }
    // Error banner is handled in shared state.
  }
}

async function refreshAudit() {
  try {
    const result = await loadAdminAuditLogs(1);
    auditLogs.value = Array.isArray(result?.results) ? result.results : [];
  } catch {
    // Error banner is handled in shared state.
  }
}

async function handleCreate() {
  try {
    const payload = parseActivityPayload(createForm);
    await createAdminActivityEntry(payload);
    await refreshList(adminPagination.value.page);
    await refreshAudit();
    createForm.title = "";
    createForm.description = "";
  } catch {
    // Error banner is handled in shared state.
  }
}

function startEdit(item) {
  editingId.value = item.id;
  hydrateEditForm(item);
}

function cancelEdit() {
  editingId.value = null;
}

async function saveEdit(itemId) {
  try {
    const payload = parseActivityPayload(editForm);
    await updateAdminActivityEntry(itemId, payload);
    editingId.value = null;
    await refreshList(adminPagination.value.page);
    await refreshAudit();
  } catch {
    // Error banner is handled in shared state.
  }
}

async function removeItem(itemId) {
  try {
    await deleteAdminActivityEntry(itemId);
    await refreshList(adminPagination.value.page);
    await refreshAudit();
  } catch {
    // Error banner is handled in shared state.
  }
}

function onCsvChange(event) {
  const file = event.target.files?.[0] || null;
  csvFile.value = file;
}

async function uploadCsv() {
  if (!csvFile.value) {
    return;
  }

  try {
    const result = await importAdminActivitiesFromCsv(csvFile.value);
    importSummary.value = result;
    csvFile.value = null;
    await refreshList(adminPagination.value.page);
    await refreshAudit();
  } catch {
    // Error banner is handled in shared state.
  }
}

onMounted(async () => {
  await refreshList(1);
  await refreshAudit();
});

async function handlePageChange(page) {
  if (state.busy.admin) {
    return;
  }
  await refreshList(page);
}
</script>

<template>
  <section class="panel history-panel wide-panel history-board-card">
    <div class="panel-heading">
      <h2>Activity Pool Admin</h2>
      <p>Maintain the activity pool with create, update, delete, and CSV import.</p>
    </div>

    <div v-if="state.formErrors.admin._form" class="form-inline-error">
      {{ state.formErrors.admin._form }}
    </div>

    <div class="admin-toolbar">
      <strong>Total: {{ totalCount }}</strong>
    </div>

    <div class="admin-grid">
      <section class="admin-form-card">
        <h3>Create activity</h3>
        <div class="stack">
          <label class="field">
            <span>Title</span>
            <input v-model="createForm.title" type="text" />
          </label>

          <label class="field">
            <span>Description</span>
            <textarea v-model="createForm.description" rows="3" />
          </label>

          <div class="admin-two-col">
            <label class="field">
              <span>Category</span>
              <input v-model="createForm.category" type="text" />
            </label>
            <label class="field">
              <span>Social</span>
              <select v-model="createForm.social_type">
                <option v-for="option in socialOptions" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
            </label>
          </div>

          <div class="admin-two-col">
            <label class="field">
              <span>Min time</span>
              <input v-model.number="createForm.min_time_minutes" type="number" min="1" />
            </label>
            <label class="field">
              <span>Max time</span>
              <input v-model.number="createForm.max_time_minutes" type="number" min="1" />
            </label>
          </div>

          <div class="admin-two-col">
            <label class="field">
              <span>Min budget</span>
              <input v-model.number="createForm.min_budget" type="number" min="0" />
            </label>
            <label class="field">
              <span>Max budget</span>
              <input v-model.number="createForm.max_budget" type="number" min="0" />
            </label>
          </div>

          <label class="field">
            <span>Mood tags (comma separated)</span>
            <input v-model="createForm.mood_tags" type="text" />
          </label>

          <div class="button-row">
            <button class="primary-button" :disabled="state.busy.admin" @click="handleCreate">
              {{ state.busy.admin ? "Saving..." : "Create" }}
            </button>
          </div>
        </div>
      </section>

      <section class="admin-form-card">
        <h3>Import CSV</h3>
        <div class="stack">
          <label class="field">
            <span>CSV file</span>
            <input type="file" accept=".csv,text/csv" @change="onCsvChange" />
          </label>
          <button
            class="primary-button"
            :disabled="state.busy.admin || !csvFile"
            @click="uploadCsv"
          >
            {{ state.busy.admin ? "Importing..." : "Import CSV" }}
          </button>

          <p v-if="importSummary" class="subtle-hint">
            Created {{ importSummary.created }}, failed {{ importSummary.failed }}.
          </p>
        </div>
      </section>
    </div>

    <ul class="history-list">
      <li v-for="item in activities" :key="item.id" class="history-item">
        <template v-if="editingId === item.id">
          <div class="admin-two-col">
            <label class="field">
              <span>Title</span>
              <input v-model="editForm.title" type="text" />
            </label>
            <label class="field">
              <span>Category</span>
              <input v-model="editForm.category" type="text" />
            </label>
          </div>
          <label class="field">
            <span>Description</span>
            <textarea v-model="editForm.description" rows="2" />
          </label>
          <div class="admin-two-col">
            <label class="field">
              <span>Min time</span>
              <input v-model.number="editForm.min_time_minutes" type="number" min="1" />
            </label>
            <label class="field">
              <span>Max time</span>
              <input v-model.number="editForm.max_time_minutes" type="number" min="1" />
            </label>
          </div>
          <div class="admin-two-col">
            <label class="field">
              <span>Min budget</span>
              <input v-model.number="editForm.min_budget" type="number" min="0" />
            </label>
            <label class="field">
              <span>Max budget</span>
              <input v-model.number="editForm.max_budget" type="number" min="0" />
            </label>
          </div>
          <label class="field">
            <span>Mood tags</span>
            <input v-model="editForm.mood_tags" type="text" />
          </label>
          <div class="admin-two-col">
            <label class="field">
              <span>Social</span>
              <select v-model="editForm.social_type">
                <option v-for="option in socialOptions" :key="option" :value="option">
                  {{ option }}
                </option>
              </select>
            </label>
            <label class="field checkbox-field">
              <input v-model="editForm.is_active" type="checkbox" />
              <span>Active</span>
            </label>
          </div>
          <div class="button-row">
            <button class="primary-button small-button" :disabled="state.busy.admin" @click="saveEdit(item.id)">
              Save
            </button>
            <button class="ghost-button small-button" :disabled="state.busy.admin" @click="cancelEdit">
              Cancel
            </button>
          </div>
        </template>

        <template v-else>
          <div class="history-head">
            <strong>{{ item.title }}</strong>
            <span class="status-pill" :class="item.is_active ? 'completed' : 'skipped'">
              {{ item.is_active ? "Active" : "Inactive" }}
            </span>
          </div>
          <p class="history-meta">
            {{ item.category }} · {{ item.min_time_minutes }}-{{ item.max_time_minutes }} min ·
            £{{ Number(item.min_budget) }}-£{{ Number(item.max_budget) }}
          </p>
          <p v-if="item.description" class="history-comment">{{ item.description }}</p>
          <div class="button-row">
            <button class="ghost-button small-button" :disabled="state.busy.admin" @click="startEdit(item)">
              Edit
            </button>
            <button class="ghost-button small-button" :disabled="state.busy.admin" @click="removeItem(item.id)">
              Delete
            </button>
          </div>
        </template>
      </li>
    </ul>

    <div v-if="activities.length && hasPagination" class="history-pagination">
      <button
        class="ghost-button"
        :disabled="state.busy.admin || adminPagination.page <= 1"
        @click="handlePageChange(adminPagination.page - 1)"
      >
        Previous
      </button>
      <strong>Page {{ adminPagination.page }} / {{ adminPagination.total_pages }}</strong>
      <button
        class="ghost-button"
        :disabled="state.busy.admin || adminPagination.page >= adminPagination.total_pages"
        @click="handlePageChange(adminPagination.page + 1)"
      >
        Next
      </button>
    </div>

    <section class="admin-form-card audit-log-card">
      <h3>Admin audit trail</h3>
      <p class="subtle-hint">Recent admin-only actions (delete/import).</p>
      <ul class="history-list">
        <li v-for="entry in auditLogs" :key="entry.id" class="history-item">
          <div class="history-head">
            <strong>{{ entry.action }}</strong>
            <span class="status-pill completed">
              {{ entry.admin_username || "system" }}
            </span>
          </div>
          <p class="history-meta">
            {{ entry.target || "n/a" }} ·
            {{ new Date(entry.created_at).toLocaleString("en-GB", { hour12: false }) }}
          </p>
        </li>
        <li v-if="!auditLogs.length" class="history-item">
          <p class="history-comment">No audit records yet.</p>
        </li>
      </ul>
    </section>
  </section>
</template>
