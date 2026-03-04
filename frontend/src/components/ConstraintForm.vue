<script setup>
import { computed, watch } from "vue";

import { EXCLUDE_CATEGORY_GROUPS } from "../categoryOptions";
import { getMoodOption, sortMoodValues } from "../moodOptions";
import { getSocialOption, sortSocialValues } from "../socialOptions";
import {
  generateSuggestion,
  hasPendingAcceptedSuggestion,
  isLoggedIn,
  resetGeneratedSuggestion,
  state,
  toggleCategoryGroup,
} from "../state";

async function handleGenerate() {
  try {
    await generateSuggestion();
  } catch {
    // Error state is handled in shared state.
  }
}

const availableMoodOptions = computed(() =>
  sortMoodValues(state.metadata.moods || []).map((mood) => getMoodOption(mood))
);
const availableSocialOptions = computed(() =>
  sortSocialValues(state.metadata.social_preferences || []).map((preference) =>
    getSocialOption(preference)
  )
);
const excludeCategoryOptions = computed(() => EXCLUDE_CATEGORY_GROUPS);

function isCategoryExcluded(category) {
  return category.rawValues.every((value) =>
    state.constraints.excluded_categories.includes(value)
  );
}

watch(
  () => [
    state.constraints.time_minutes,
    state.constraints.budget,
    state.constraints.mood,
    state.constraints.social_preference,
    state.constraints.excluded_categories.join("|"),
  ],
  () => {
    resetGeneratedSuggestion();
  }
);
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <h2>Set your limits</h2>
      <p>We’ll take it from there.</p>
    </div>

    <div class="stack">
      <p v-if="state.formErrors.constraints._form" class="form-inline-error">
        {{ state.formErrors.constraints._form }}
      </p>

      <div class="form-section">
        <p class="section-kicker">1. Your Mood</p>
        <p class="section-note">Choose the energy level you want the activity to match.</p>
        <div class="field">
          <span>How are you feeling today?</span>
          <div
            class="mood-choice-list"
            :class="{ 'invalid-input': state.formErrors.constraints.mood }"
            role="radiogroup"
            aria-label="How are you feeling today?"
          >
            <button
              v-for="mood in availableMoodOptions"
              :key="mood.value"
              type="button"
              class="mood-choice"
              :class="{ active: state.constraints.mood === mood.value }"
              :aria-pressed="state.constraints.mood === mood.value"
              @click="state.constraints.mood = mood.value"
            >
              <span
                class="mood-radio"
                :class="{ active: state.constraints.mood === mood.value }"
                aria-hidden="true"
              />
              <span class="mood-copy">
                {{ mood.label }}
              </span>
            </button>
          </div>
          <small v-if="state.formErrors.constraints.mood" class="field-error">
            {{ state.formErrors.constraints.mood }}
          </small>
        </div>
      </div>

      <div class="form-section">
        <p class="section-kicker">2. Available Time</p>
        <p class="section-note">Examples: 10 min, 30 min, or 1 hour.</p>
        <label class="field">
          <span>How much time do you have?</span>
          <input
            v-model.number="state.constraints.time_minutes"
            type="number"
            min="5"
            max="1440"
            step="5"
            placeholder="60"
            :class="{ 'invalid-input': state.formErrors.constraints.time_minutes }"
          />
          <small v-if="state.formErrors.constraints.time_minutes" class="field-error">
            {{ state.formErrors.constraints.time_minutes }}
          </small>
        </label>

        <label class="field">
          <span>What's your budget?</span>
          <div class="currency-field">
            <span class="currency-prefix">£</span>
            <input
              v-model="state.constraints.budget"
              type="number"
              min="0"
              step="1"
              placeholder="20"
              :class="{ 'invalid-input': state.formErrors.constraints.budget }"
            />
          </div>
          <small v-if="state.formErrors.constraints.budget" class="field-error">
            {{ state.formErrors.constraints.budget }}
          </small>
        </label>
      </div>

      <div class="form-section">
        <p class="section-kicker">3. Social Preference</p>
        <p class="section-note">Pick who you want this activity to work for.</p>
        <div class="field">
          <span>Who’s joining?</span>
          <div
            class="mood-choice-list"
            :class="{ 'invalid-input': state.formErrors.constraints.social_preference }"
            role="radiogroup"
            aria-label="Who’s joining?"
          >
            <button
              v-for="preference in availableSocialOptions"
              :key="preference.value"
              type="button"
              class="mood-choice"
              :class="{ active: state.constraints.social_preference === preference.value }"
              :aria-pressed="state.constraints.social_preference === preference.value"
              @click="state.constraints.social_preference = preference.value"
            >
              <span
                class="mood-radio"
                :class="{ active: state.constraints.social_preference === preference.value }"
                aria-hidden="true"
              />
              <span class="mood-copy">
                {{ preference.label }}
              </span>
            </button>
          </div>
          <small
            v-if="state.formErrors.constraints.social_preference"
            class="field-error"
          >
            {{ state.formErrors.constraints.social_preference }}
          </small>
        </div>
      </div>

      <div class="form-section">
        <p class="section-kicker">4. Excluded Categories</p>
        <p class="section-note">Remove anything you definitely do not want right now.</p>
        <div class="field">
          <span>Excluded categories</span>
          <small class="field-note">
            These are hard filters. If nothing fits, we’ll relax this once.
          </small>
          <div class="tag-grid">
            <button
              v-for="category in excludeCategoryOptions"
              :key="category.key"
              type="button"
              class="tag-button"
              :class="{ active: isCategoryExcluded(category) }"
              @click="toggleCategoryGroup(category.rawValues)"
            >
              {{ isCategoryExcluded(category) ? "❌ " : "" }}{{ category.label }}
            </button>
          </div>
        </div>
      </div>

      <div class="button-row">
        <p
          v-if="hasPendingAcceptedSuggestion"
          class="inline-hint"
        >
          You already accepted an activity. Log it in Activity History before
          generating another one.
        </p>

        <button
          class="primary-button generate-button"
          :disabled="!isLoggedIn || state.busy.generate || hasPendingAcceptedSuggestion"
          @click="handleGenerate"
        >
          {{
            hasPendingAcceptedSuggestion
              ? "Log current activity first"
              : state.busy.generate
                ? "Generating activity..."
                : "✨ Generate Activity"
          }}
        </button>
      </div>
    </div>
  </section>
</template>
