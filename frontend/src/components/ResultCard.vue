<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import CalendarModal from "./CalendarModal.vue";
import { getCategoryOption } from "../categoryOptions";
import { getSocialOption } from "../socialOptions";
import {
  acceptCurrentSuggestion,
  canReroll,
  rerollSuggestion,
  saveCurrentSuggestion,
  state,
} from "../state";

const props = defineProps({
  embedded: {
    type: Boolean,
    default: false,
  },
});

const actionsDisabled = computed(
  () => state.busy.generate || state.busy.accept || state.busy.saved
);
const rerollButtonDisabled = computed(
  () => actionsDisabled.value || !canReroll.value || Boolean(state.suggestion?.is_accepted)
);
const acceptButtonDisabled = computed(
  () => actionsDisabled.value || Boolean(state.suggestion?.is_accepted)
);
const calendarOpen = ref(false);
const popResultCard = ref(false);
let popTimerId = null;

const TITLE_EMOJI_MAP = {
  FOOD: "🍽",
  INDOOR: "🏠",
  OUTDOOR: "🌤",
  FITNESS: "🏃",
  CULTURE: "🎨",
  CLASS: "📚",
  SOCIAL: "👥",
  HOME: "🛋",
};

function stripLeadingEmoji(label) {
  return String(label || "")
    .replace(/^[^\p{L}\p{N}]+/u, "")
    .trim();
}

const resultTitle = computed(() => {
  if (!state.suggestion) {
    return "";
  }
  const category = String(state.suggestion.activity.category || "").toUpperCase();
  const emoji = TITLE_EMOJI_MAP[category] || "✨";
  return `${emoji} ${state.suggestion.activity.title}`;
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

async function handleSave() {
  if (!state.suggestion) {
    return;
  }

  try {
    await saveCurrentSuggestion();
  } catch {
    // Error state is handled in shared state.
  }
}

function handleOpenCalendar() {
  calendarOpen.value = true;
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

watch(
  () =>
    state.suggestion
      ? `${state.suggestion.id}-${state.suggestion.is_accepted ? "accepted" : "review"}`
      : "",
  (current, previous) => {
    if (!current || current === previous) {
      return;
    }
    popResultCard.value = true;
    if (popTimerId) {
      window.clearTimeout(popTimerId);
    }
    popTimerId = window.setTimeout(() => {
      popResultCard.value = false;
      popTimerId = null;
    }, 520);
  }
);

onBeforeUnmount(() => {
  if (popTimerId) {
    window.clearTimeout(popTimerId);
    popTimerId = null;
  }
});
</script>

<template>
  <section
    :id="props.embedded ? undefined : 'result-panel'"
    class="panel result-panel result-board-card"
    :class="{ 'result-panel-embedded': props.embedded }"
  >
    <div v-if="!props.embedded" class="panel-heading">
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
          class="result-card suggestion-sticker"
          :class="{
            'accepted-card': state.suggestion.is_accepted,
            'fresh-pop': popResultCard,
          }"
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

          <h3>{{ resultTitle }}</h3>
          <p class="result-copy">{{ state.suggestion.activity.description }}</p>

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

          <div v-if="!state.suggestion.is_accepted" class="result-actions-stack">
            <div class="result-secondary-row">
              <button
                class="ghost-button result-secondary-button"
                :disabled="rerollButtonDisabled"
                @click="handleReroll"
              >
                {{ state.busy.generate ? "Generating..." : "🎲 Another one" }}
              </button>

              <button
                class="ghost-button result-secondary-button"
                :disabled="actionsDisabled"
                @click="handleSave"
              >
                {{ state.busy.saved ? "Saving..." : "💾 Save" }}
              </button>
            </div>

            <button
              class="primary-button result-accept-button"
              :disabled="acceptButtonDisabled"
              @click="handleAccept"
            >
              {{ state.busy.accept ? "Working..." : "✅ Accept" }}
            </button>

            <button
              class="result-calendar-link"
              :disabled="actionsDisabled"
              @click="handleOpenCalendar"
            >
              📅 Add to calendar
            </button>
          </div>

          <div v-else class="accepted-guidance" role="status">
            <strong>Next step</strong>
            <p>Head to Activity History and mark this as done or skipped.</p>
            <button class="ghost-button small-button" @click="handleOpenCalendar">
              Add to Calendar
            </button>
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

      <div v-else key="result-empty" class="empty-state sticker-empty-card">
        <div class="result-mascot" aria-hidden="true">🤖</div>
        <div class="result-bubble">Tell me your mood, time, and budget level. I’ll pitch one idea.</div>
        <p class="sticker-empty-copy">No suggestion yet. Fill your limits and hit ✨ Surprise me.</p>
      </div>
    </Transition>

    <CalendarModal
      v-model="calendarOpen"
      :activity="state.suggestion?.activity || null"
    />
  </section>
</template>
