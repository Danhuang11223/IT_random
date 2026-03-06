<script setup>
import { computed, ref } from "vue";
import { RouterLink } from "vue-router";

import { getBudgetOption } from "../budgetOptions";
import CalendarModal from "./CalendarModal.vue";
import { getCategoryOption } from "../categoryOptions";
import { getMoodOption } from "../moodOptions";
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
  const budget = state.constraints.budget_preference
    ? getBudgetOption(state.constraints.budget_preference).label.toLowerCase()
    : "your budget";
  const time = getTimeDescriptor(Number(state.constraints.time_minutes || 0));

  return `Based on your ${mood} mood, ${time} available time, ${budget} range, and ${social} preference.`;
});

const explainability = computed(() => state.suggestion?.explainability || null);
const resultTitle = computed(() => {
  if (!state.suggestion) {
    return "";
  }
  const category = String(state.suggestion.activity.category || "").toUpperCase();
  const emoji = TITLE_EMOJI_MAP[category] || "✨";
  return `${emoji} ${state.suggestion.activity.title}`;
});

const energyScoreLabel = computed(() => {
  const score = explainability.value?.soft_preferences?.energy?.score ?? 0;
  return `+${score}/2`;
});

const socialScoreLabel = computed(() => {
  const score = explainability.value?.soft_preferences?.social?.score ?? 0;
  return `+${score}/1`;
});

function explainabilityStatus(value) {
  return value ? "Matched" : "Not matched";
}

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

          <h3>{{ resultTitle }}</h3>
          <p class="result-copy">{{ state.suggestion.activity.description }}</p>
          <div class="why-card">
            <strong>Why this activity?</strong>
            <p>{{ whyThisActivity }}</p>
          </div>

          <details v-if="explainability" class="explainability-card">
            <summary>Why this suggestion</summary>

            <div class="explainability-block">
              <p class="explainability-title">Hard constraints</p>
              <ul>
                <li>
                  Time:
                  {{ explainabilityStatus(explainability.hard_constraints.time.matched) }}
                  (need ≤ {{ explainability.hard_constraints.time.required_minutes }} min,
                  activity min {{ explainability.hard_constraints.time.activity_min_minutes }} min)
                </li>
                <li>
                  Budget:
                  {{ explainabilityStatus(explainability.hard_constraints.budget.matched) }}
                  (budget ≤ £{{ explainability.hard_constraints.budget.required_budget }},
                  activity max £{{ explainability.hard_constraints.budget.activity_max_budget }})
                </li>
                <li>
                  Category:
                  {{
                    explainability.hard_constraints.excluded_category.relaxed
                      ? "Relaxed once"
                      : explainabilityStatus(
                        explainability.hard_constraints.excluded_category.matched
                      )
                  }}
                  (activity: {{ explainability.hard_constraints.excluded_category.activity_category }})
                </li>
              </ul>
            </div>

            <div class="explainability-block">
              <p class="explainability-title">Soft preference score</p>
              <ul>
                <li>
                  Energy:
                  {{ explainabilityStatus(explainability.soft_preferences.energy.matched) }}
                  {{ energyScoreLabel }}
                </li>
                <li>
                  Social:
                  {{ explainabilityStatus(explainability.soft_preferences.social.matched) }}
                  {{ socialScoreLabel }}
                </li>
                <li>
                  Total score:
                  {{ explainability.soft_preferences.total_score }}
                  / {{ explainability.soft_preferences.max_score }}
                </li>
              </ul>
            </div>

            <div class="explainability-block">
              <p class="explainability-title">System decisions</p>
              <ul>
                <li>
                  Category fallback:
                  {{
                    explainability.system.fallback_applied
                      ? "Applied"
                      : "Not applied"
                  }}
                </li>
                <li>
                  Cooldown relaxed:
                  {{
                    explainability.system.cooldown_relaxed
                      ? "Applied once"
                      : "Not applied"
                  }}
                </li>
              </ul>
            </div>
          </details>

          <p
            v-if="state.suggestion.fallback_applied && state.suggestion.fallback_message"
            class="inline-hint"
          >
            {{ state.suggestion.fallback_message }}
          </p>
          <p
            v-if="state.suggestion.cooldown_relaxed && state.suggestion.cooldown_message"
            class="inline-hint"
          >
            {{ state.suggestion.cooldown_message }}
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
              {{ state.busy.generate ? "Generating..." : "🎲 Another one" }}
            </button>

            <button
              class="primary-button"
              :disabled="acceptButtonDisabled"
              @click="handleAccept"
            >
              {{ state.busy.accept ? "Working..." : "✅ Accept" }}
            </button>

            <button
              class="ghost-button"
              :disabled="actionsDisabled"
              @click="handleSave"
            >
              {{ state.busy.saved ? "Saving..." : "💾 Save" }}
            </button>

            <button
              class="ghost-button"
              :disabled="actionsDisabled"
              @click="handleOpenCalendar"
            >
              📅 Add to Calendar
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
