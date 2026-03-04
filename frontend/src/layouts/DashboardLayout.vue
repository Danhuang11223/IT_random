<script setup>
import { computed } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";

import { getMoodOption } from "../moodOptions";
import { getSocialOption } from "../socialOptions";
import { logout, state } from "../state";

const router = useRouter();

function stripLeadingEmoji(label) {
  return String(label || "")
    .replace(/^[^\p{L}\p{N}]+/u, "")
    .trim();
}

const energySummary = computed(() => {
  if (!state.constraints.mood) {
    return "Not selected";
  }

  return stripLeadingEmoji(getMoodOption(state.constraints.mood).label);
});

const timeSummary = computed(() => {
  if (!state.constraints.time_minutes) {
    return "Not set";
  }

  return `${state.constraints.time_minutes} min`;
});

const socialSummary = computed(() => {
  if (!state.constraints.social_preference) {
    return "Not selected";
  }

  return stripLeadingEmoji(getSocialOption(state.constraints.social_preference).label);
});

function handleLogout() {
  logout();
  router.push("/login");
}
</script>

<template>
  <section class="dashboard-layout">
    <header class="dashboard-header">
      <div class="dashboard-header-copy">
        <p class="eyebrow">Decision Support</p>
        <h1>Random Activity Flow</h1>
        <p class="dashboard-subcopy">
          Set your limits, review a suggestion, then mark it as done or skip it
          later.
        </p>
      </div>

      <div class="dashboard-header-side">
        <nav class="nav-links">
          <RouterLink to="/dashboard">Generator</RouterLink>
          <RouterLink to="/history">Activity History</RouterLink>
        </nav>

        <div class="user-badge">
          <span>{{ state.user?.username || "Signed-in user" }}</span>
          <button class="ghost-button" @click="handleLogout">Sign out</button>
        </div>
      </div>
    </header>

    <section class="dashboard-summary">
      <div class="summary-card">
        <span>Energy level</span>
        <strong>Energy: {{ energySummary }}</strong>
      </div>
      <div class="summary-card">
        <span>Time available</span>
        <strong>Time: {{ timeSummary }}</strong>
      </div>
      <div class="summary-card">
        <span>Social mode</span>
        <strong>Social: {{ socialSummary }}</strong>
      </div>
    </section>

    <div class="dashboard-stage">
      <RouterView />
    </div>
  </section>
</template>
