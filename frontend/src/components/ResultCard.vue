<script setup>
import { computed } from "vue";
import { RouterLink } from "vue-router";

import { getCategoryOption } from "../categoryOptions";
import { getMoodOption } from "../moodOptions";
import { getSocialOption } from "../socialOptions";
import {
  acceptCurrentSuggestion,
  canReroll,
  rerollSuggestion,
  state,
} from "../state";

const actionsDisabled = computed(() => state.busy.generate || state.busy.accept);
const rerollButtonDisabled = computed(
  () => actionsDisabled.value || !canReroll.value || Boolean(state.suggestion?.is_accepted)
);
const acceptButtonDisabled = computed(
  () => actionsDisabled.value || Boolean(state.suggestion?.is_accepted)
);

function stripLeadingEmoji(label) {
  return String(label || "")
    .replace(/^[^\p{L}\p{N}]+/u, "")
    .trim();
}

function getTimeDescriptor(minutes) {
  if (!minutes) {
    return "open-ended";
  }

  if (minutes <= 20) {
    return "short";
  }

  if (minutes <= 60) {
    return "manageable";
  }

  return "longer";
}

const whyThisActivity = computed(() => {
  if (!state.suggestion) {
    return "";
  }

  const mood = state.constraints.mood
    ? stripLeadingEmoji(getMoodOption(state.constraints.mood).label).toLowerCase()
    : "current";
  const social = state.constraints.social_preference
    ? stripLeadingEmoji(getSocialOption(state.constraints.social_preference).label).toLowerCase()
    : "your preference";
  const time = getTimeDescriptor(Number(state.constraints.time_minutes || 0));

  return `Based on your ${mood} mood, ${time} available time, and ${social} preference.`;
});

async function handleAccept() {
  try {
    await acceptCurrentSuggestion();
  } catch {
    // Error state is handled in shared state.
  }
}

async function handleReroll() {
  try {
    await rerollSuggestion();
  } catch {
    // Error state is handled in shared state.
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

function formatSocialLabel(socialType) {
  return stripLeadingEmoji(getSocialOption(socialType).label);
}
</script>

<template>
  <section class="panel result-panel">
    <div class="panel-heading">
      <h2>Your Suggestion</h2>
      <p>Your generated activity will appear here. Accept it or try another one.</p>
    </div>

    <Transition name="result-swap" mode="out-in">
      <div
        v-if="state.suggestion"
        :key="`suggestion-${state.suggestion.id}-${state.suggestion.is_accepted}`"
        class="result-shell"
      >
        <div
          class="result-card"
          :class="{ 'accepted-card': state.suggestion.is_accepted }"
        >
          <div class="result-headline">
            <p class="result-category">
              {{ getCategoryOption(state.suggestion.activity.category).label }}
            </p>
            <span
              class="live-result-pill"
              :class="{ accepted: state.suggestion.is_accepted }"
            >
              {{ state.suggestion.is_accepted ? "Accepted" : "Review" }}
            </span>
          </div>

          <h3>{{ state.suggestion.activity.title }}</h3>
          <p class="result-copy">{{ state.suggestion.activity.description }}</p>
          <div class="why-card">
            <strong>Why this activity?</strong>
            <p>{{ whyThisActivity }}</p>
          </div>
          <p
            v-if="state.suggestion.fallback_applied && state.suggestion.fallback_message"
            class="inline-hint"
          >
            {{ state.suggestion.fallback_message }}
          </p>

          <dl class="metrics">
            <div>
              <dt>Estimated Time</dt>
              <dd>
                {{ state.suggestion.activity.min_time_minutes }} -
                {{ state.suggestion.activity.max_time_minutes }} min
              </dd>
            </div>
            <div>
              <dt>Estimated Budget</dt>
              <dd>{{ formatBudgetRange(state.suggestion.activity) }}</dd>
            </div>
            <div>
              <dt>Social</dt>
              <dd>{{ formatSocialLabel(state.suggestion.activity.social_type) }}</dd>
            </div>
          </dl>

          <div v-if="!state.suggestion.is_accepted" class="button-row">
            <button
              class="ghost-button"
              :disabled="rerollButtonDisabled"
              @click="handleReroll"
            >
              {{ state.busy.generate ? "Generating..." : "Generate another activity" }}
            </button>

            <button
              class="primary-button"
              :disabled="acceptButtonDisabled"
              @click="handleAccept"
            >
              {{ state.busy.accept ? "Working..." : "Accept" }}
            </button>
          </div>

          <div v-else class="accepted-guidance" role="status">
            <strong>Next step</strong>
            <p>Head to Activity History and mark this as done or skipped.</p>
            <RouterLink class="primary-link" to="/history">Open history</RouterLink>
          </div>
        </div>
      </div>

      <div
        v-else-if="state.busy.generate"
        key="result-loading"
        class="result-card skeleton-card"
      >
        <div class="skeleton-row skeleton-pill" />
        <div class="skeleton-row skeleton-title" />
        <div class="skeleton-row skeleton-text short" />
        <div class="skeleton-row skeleton-text" />

        <div class="skeleton-metrics">
          <div class="skeleton-metric" />
          <div class="skeleton-metric" />
          <div class="skeleton-metric" />
        </div>

        <div class="skeleton-button-row">
          <div class="skeleton-button ghost" />
          <div class="skeleton-button" />
        </div>
      </div>

      <div v-else-if="state.pendingLog" key="result-pending" class="empty-state">
        <p>You already have an accepted activity waiting to be logged.</p>
        <RouterLink class="primary-link" to="/history">Open history</RouterLink>
      </div>

      <div v-else key="result-empty" class="empty-state">
        <p>No suggestion yet. Fill in your limits and hit ✨ Generate Activity.</p>
      </div>
    </Transition>
  </section>
</template>
