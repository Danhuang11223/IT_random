<script setup>
import { RouterView } from "vue-router";

import { retryLastRequest, state } from "./state";
</script>

<template>
  <div class="root-shell">
    <div v-if="state.error" class="notice-stack">
      <div class="status-banner error retry-banner">
        <span>{{ state.error }}</span>
        <button
          v-if="state.retryAction"
          class="ghost-button retry-button"
          :disabled="state.busy.retry"
          @click="retryLastRequest"
        >
          {{ state.busy.retry ? "重试中..." : state.retryLabel || "重试" }}
        </button>
      </div>
    </div>

    <RouterView />
  </div>
</template>
