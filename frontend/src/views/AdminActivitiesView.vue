<script setup>
import { onMounted } from "vue";

import AdminActivityManager from "../components/AdminActivityManager.vue";
import { loadDashboardData, state } from "../state";

onMounted(async () => {
  if (state.dashboardReady) {
    return;
  }

  try {
    await loadDashboardData({ force: true });
  } catch {
    // Error banner is handled in global state.
  }
});
</script>

<template>
  <main class="single-column history-flow">
    <AdminActivityManager />
  </main>
</template>
