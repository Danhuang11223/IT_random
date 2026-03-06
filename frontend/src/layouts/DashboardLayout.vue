<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";

import { getBudgetOption } from "../budgetOptions";
import { getMoodOption } from "../moodOptions";
import { getSocialOption } from "../socialOptions";
import { logout, state, toggleUiPreference } from "../state";

const router = useRouter();
const a11yOpen = ref(false);
const profileOpen = ref(false);
const a11yRef = ref(null);
const profileRef = ref(null);

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
  profileOpen.value = false;
  router.push("/login");
}

function closeMenus() {
  a11yOpen.value = false;
  profileOpen.value = false;
}

function toggleA11yMenu() {
  a11yOpen.value = !a11yOpen.value;
  if (a11yOpen.value) {
    profileOpen.value = false;
  }
}

function toggleProfileMenu() {
  profileOpen.value = !profileOpen.value;
  if (profileOpen.value) {
    a11yOpen.value = false;
  }
}

function handleDocumentClick(event) {
  const target = event.target;
  if (a11yRef.value && !a11yRef.value.contains(target)) {
    a11yOpen.value = false;
  }
  if (profileRef.value && !profileRef.value.contains(target)) {
    profileOpen.value = false;
  }
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

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", handleDocumentClick);
  document.removeEventListener("keydown", handleEscape);
});
</script>

<template>
  <section class="dashboard-layout">
    <header class="dashboard-header">
      <div class="dashboard-header-copy">
        <p class="eyebrow">Decision Support</p>
        <h1>Random Activity</h1>
        <p class="dashboard-subcopy">Set limits, get one fun next move.</p>
      </div>

      <div class="dashboard-header-side">
        <nav class="nav-links">
          <RouterLink to="/dashboard">Generator</RouterLink>
          <RouterLink to="/history">Activity History</RouterLink>
          <RouterLink to="/saved">Saved</RouterLink>
        </nav>

        <div ref="a11yRef" class="a11y-menu">
          <button
            type="button"
            class="ghost-button a11y-trigger"
            :aria-expanded="a11yOpen"
            aria-controls="a11y-dropdown"
            @click="toggleA11yMenu"
          >
            Accessibility
          </button>
          <div
            v-if="a11yOpen"
            id="a11y-dropdown"
            class="a11y-dropdown"
            role="group"
            aria-label="Accessibility settings"
          >
            <button
              type="button"
              class="a11y-switch"
              role="switch"
              :aria-checked="state.uiPrefs.reduceMotion"
              @click="toggleUiPreference('reduceMotion')"
            >
              <span>Reduce motion</span>
              <span class="switch-pill" :class="{ active: state.uiPrefs.reduceMotion }" />
            </button>
            <button
              type="button"
              class="a11y-switch"
              role="switch"
              :aria-checked="state.uiPrefs.largerText"
              @click="toggleUiPreference('largerText')"
            >
              <span>Larger text</span>
              <span class="switch-pill" :class="{ active: state.uiPrefs.largerText }" />
            </button>
            <button
              type="button"
              class="a11y-switch"
              role="switch"
              :aria-checked="state.uiPrefs.highContrast"
              @click="toggleUiPreference('highContrast')"
            >
              <span>High contrast</span>
              <span class="switch-pill" :class="{ active: state.uiPrefs.highContrast }" />
            </button>
          </div>
        </div>

        <div ref="profileRef" class="profile-menu">
          <button
            type="button"
            class="profile-trigger"
            :aria-expanded="profileOpen"
            aria-controls="profile-dropdown"
            @click="toggleProfileMenu"
          >
            <span class="avatar-circle">{{ userInitial }}</span>
            <span class="profile-name">{{ state.user?.username || "Signed-in user" }}</span>
          </button>
          <div
            v-if="profileOpen"
            id="profile-dropdown"
            class="profile-dropdown"
          >
            <button class="ghost-button profile-signout" @click="handleLogout">
              Sign out
            </button>
          </div>
        </div>
      </div>
    </header>

    <section class="filter-strip">
      <span class="filter-label">Current filters</span>
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
