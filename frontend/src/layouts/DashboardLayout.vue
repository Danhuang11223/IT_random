<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";

import diceIcon from "../assets/dice-random.svg";
import { getBudgetOption } from "../budgetOptions";
import { getMoodOption } from "../moodOptions";
import { getSocialOption } from "../socialOptions";
import { logout, state, toggleUiPreference } from "../state";

const router = useRouter();
const route = useRoute();
const settingsOpen = ref(false);
const settingsA11yOpen = ref(false);
const settingsRef = ref(null);

const energySummary = computed(() => {
  if (!state.constraints.mood) {
    return "🌿 Not selected";
  }

  return getMoodOption(state.constraints.mood).label;
});

const timeSummary = computed(() => {
  if (!state.constraints.time_minutes) {
    return "⏱ Not set";
  }

  return `⏱ ${state.constraints.time_minutes} min`;
});

const socialSummary = computed(() => {
  if (!state.constraints.social_preference) {
    return "👥 Not selected";
  }

  return getSocialOption(state.constraints.social_preference).label;
});

const budgetSummary = computed(() => {
  if (!state.constraints.budget_preference) {
    return "💰 Not selected";
  }

  return `💰 ${getBudgetOption(state.constraints.budget_preference).label}`;
});

const userInitial = computed(() => {
  const username = String(state.user?.username || "").trim();
  return username ? username[0].toUpperCase() : "U";
});

function handleLogout() {
  logout();
  settingsOpen.value = false;
  settingsA11yOpen.value = false;
  router.push("/login");
}

function closeMenus() {
  settingsOpen.value = false;
  settingsA11yOpen.value = false;
}

function handleDocumentClick(event) {
  const target = event.target;
  if (settingsRef.value && !settingsRef.value.contains(target)) {
    settingsOpen.value = false;
  }
}

function toggleSettingsMenu() {
  settingsOpen.value = !settingsOpen.value;
  if (!settingsOpen.value) {
    settingsA11yOpen.value = false;
  }
}

function toggleSettingsA11y() {
  settingsA11yOpen.value = !settingsA11yOpen.value;
}

function handleEscape(event) {
  if (event.key === "Escape") {
    closeMenus();
  }
}

onMounted(() => {
  document.addEventListener("mousedown", handleDocumentClick);
  document.addEventListener("keydown", handleEscape);
});

watch(
  () => route.fullPath,
  () => {
    closeMenus();
  }
);

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", handleDocumentClick);
  document.removeEventListener("keydown", handleEscape);
});
</script>

<template>
  <section class="dashboard-layout">
    <div class="scene-layer" aria-hidden="true">
      <span class="scene-blob blob-a" />
      <span class="scene-blob blob-b" />
      <span class="scene-blob blob-c" />
      <span class="scene-doodle doodle-a">✨</span>
      <span class="scene-doodle doodle-b">🎲</span>
      <span class="scene-doodle doodle-c">🍃</span>
    </div>

    <header class="dashboard-header">
      <div class="dashboard-brand">
        <img :src="diceIcon" alt="" class="dashboard-brand-icon" />
        <div class="dashboard-header-copy">
          <p class="eyebrow">Decision Support</p>
          <h1>Random Activity</h1>
          <p class="dashboard-subcopy">Set your limits and discover something fun.</p>
        </div>
      </div>

      <div class="dashboard-header-side">
        <nav class="nav-links">
          <RouterLink to="/dashboard">Generator</RouterLink>
          <RouterLink to="/history">Activity History</RouterLink>
          <RouterLink to="/saved">Saved</RouterLink>
        </nav>

        <div ref="settingsRef" class="profile-menu settings-menu">
          <button
            type="button"
            class="profile-trigger settings-trigger"
            :aria-expanded="settingsOpen"
            aria-controls="settings-dropdown"
            aria-label="Open settings"
            @click="toggleSettingsMenu"
          >
            <span class="avatar-circle">{{ userInitial }}</span>
          </button>
          <div
            v-if="settingsOpen"
            id="settings-dropdown"
            class="profile-dropdown settings-dropdown"
            role="menu"
            aria-label="Account settings"
          >
            <p class="settings-row settings-account-row">Account ({{ state.user?.username || "admin" }})</p>
            <button
              type="button"
              class="settings-row settings-accessibility-row"
              :aria-expanded="settingsA11yOpen"
              aria-controls="settings-a11y-panel"
              @click="toggleSettingsA11y"
            >
              <span>Accessibility</span>
              <span class="settings-chevron" :class="{ open: settingsA11yOpen }">⌄</span>
            </button>
            <div
              v-if="settingsA11yOpen"
              id="settings-a11y-panel"
              class="settings-a11y-panel"
            >
              <button
                type="button"
                class="a11y-switch settings-switch"
                role="switch"
                :aria-checked="state.uiPrefs.reduceMotion"
                @click="toggleUiPreference('reduceMotion')"
              >
                <span>Reduce motion</span>
                <span class="switch-pill" :class="{ active: state.uiPrefs.reduceMotion }" />
              </button>
              <button
                type="button"
                class="a11y-switch settings-switch"
                role="switch"
                :aria-checked="state.uiPrefs.largerText"
                @click="toggleUiPreference('largerText')"
              >
                <span>Larger text</span>
                <span class="switch-pill" :class="{ active: state.uiPrefs.largerText }" />
              </button>
              <button
                type="button"
                class="a11y-switch settings-switch"
                role="switch"
                :aria-checked="state.uiPrefs.highContrast"
                @click="toggleUiPreference('highContrast')"
              >
                <span>High contrast</span>
                <span class="switch-pill" :class="{ active: state.uiPrefs.highContrast }" />
              </button>
            </div>
            <button class="settings-row settings-logout-row" @click="handleLogout">
              Log out
            </button>
          </div>
        </div>
      </div>
    </header>

    <section class="filter-strip">
      <span class="filter-label">Your choices</span>
      <div class="filter-pills">
        <div class="filter-pill icon-pill">
          <span>{{ energySummary }}</span>
        </div>
        <div class="filter-pill icon-pill">
          <span>{{ timeSummary }}</span>
        </div>
        <div class="filter-pill icon-pill">
          <span>{{ socialSummary }}</span>
        </div>
        <div class="filter-pill icon-pill">
          <span>{{ budgetSummary }}</span>
        </div>
      </div>
    </section>

    <div class="dashboard-stage">
      <RouterView />
    </div>
  </section>
</template>
