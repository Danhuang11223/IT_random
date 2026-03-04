<script setup>
import { onMounted } from "vue";

import ConstraintForm from "../components/ConstraintForm.vue";
import ResultCard from "../components/ResultCard.vue";
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
  <main class="layout dashboard-flow">
    <ConstraintForm />
    <ResultCard />
  </main>
</template>
