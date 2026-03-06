<script setup>
import { computed, ref, watch } from "vue";

import { getBudgetOption, getBudgetOptions } from "../budgetOptions";
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
import CategoryIcon from "./CategoryIcon.vue";
import ResultCard from "./ResultCard.vue";

const wizardSteps = [
  { key: "mood", label: "Mood" },
  { key: "time", label: "Time" },
  { key: "budget", label: "Budget" },
  { key: "social", label: "Social" },
  { key: "surprise", label: "Surprise" },
  { key: "result", label: "Result" },
];

const STEP_INDEX = {
  mood: 0,
  time: 1,
  budget: 2,
  social: 3,
  surprise: 4,
  result: 5,
};

const quickTimeChoices = [5, 15, 30, 60];
const wizardStepIndex = ref(0);
const wizardDirection = ref("forward");
const wizardError = ref("");
const timeMode = ref("quick");

const availableMoodOptions = computed(() =>
  sortMoodValues(state.metadata.moods || []).map((mood) => getMoodOption(mood))
);
const availableSocialOptions = computed(() =>
  sortSocialValues(state.metadata.social_preferences || []).map((preference) =>
    getSocialOption(preference)
  )
);
const budgetOptions = getBudgetOptions();
const excludeCategoryOptions = computed(() => EXCLUDE_CATEGORY_GROUPS);
const currentWizardStep = computed(() => wizardSteps[wizardStepIndex.value]);
const wizardProgress = computed(
  () => `${wizardStepIndex.value + 1} / ${wizardSteps.length}`
);
const stepTransitionName = computed(() =>
  wizardDirection.value === "forward" ? "wizard-slide-left" : "wizard-slide-right"
);

const selectedMoodLabel = computed(() =>
  state.constraints.mood ? getMoodOption(state.constraints.mood).label : "Not selected"
);
const selectedBudgetLabel = computed(() =>
  state.constraints.budget_preference
    ? getBudgetOption(state.constraints.budget_preference).label
    : "Not selected"
);
const selectedSocialLabel = computed(() =>
  state.constraints.social_preference
    ? getSocialOption(state.constraints.social_preference).label
    : "Not selected"
);

function isCategoryExcluded(category) {
  return category.rawValues.every((value) =>
    state.constraints.excluded_categories.includes(value)
  );
}

function isQuickTimeActive(minutes) {
  return Number(state.constraints.time_minutes) === minutes;
}

function setWizardStep(index, direction = "forward") {
  if (index < 0 || index >= wizardSteps.length) {
    return;
  }
  wizardDirection.value = direction;
  wizardStepIndex.value = index;
  wizardError.value = "";
}

function jumpToStep(index) {
  if (index === wizardStepIndex.value) {
    return;
  }

  setWizardStep(index, index > wizardStepIndex.value ? "forward" : "backward");
}

function goPreviousStep() {
  setWizardStep(wizardStepIndex.value - 1, "backward");
}

function isValidTimeSelection() {
  const rawTimeValue = String(state.constraints.time_minutes ?? "").trim();
  if (!rawTimeValue) {
    return false;
  }
  const timeValue = Number(rawTimeValue);
  return (
    Number.isInteger(timeValue)
    && timeValue >= 5
    && timeValue <= 1440
    && timeValue % 5 === 0
  );
}

function stepErrorMessage(stepKey) {
  if (stepKey === "mood") {
    return "Pick one mood to continue.";
  }
  if (stepKey === "time") {
    return "Choose a time value in 5-minute increments.";
  }
  if (stepKey === "budget") {
    return "Pick a budget level to continue.";
  }
  if (stepKey === "social") {
    return "Select who is joining.";
  }
  return "";
}

function isStepReady(stepKey) {
  if (stepKey === "mood") {
    return Boolean(state.constraints.mood);
  }
  if (stepKey === "time") {
    return isValidTimeSelection();
  }
  if (stepKey === "budget") {
    return Boolean(state.constraints.budget_preference);
  }
  if (stepKey === "social") {
    return Boolean(state.constraints.social_preference);
  }
  return true;
}

function goNextStep() {
  const stepKey = currentWizardStep.value.key;
  if (!isStepReady(stepKey)) {
    wizardError.value = stepErrorMessage(stepKey);
    return;
  }
  setWizardStep(wizardStepIndex.value + 1, "forward");
}

function queueAutoAdvance(expectedStepKey) {
  window.setTimeout(() => {
    if (currentWizardStep.value.key !== expectedStepKey) {
      return;
    }
    goNextStep();
  }, 160);
}

function handleMoodSelect(value) {
  state.constraints.mood = value;
  wizardError.value = "";
  queueAutoAdvance("mood");
}

function handleBudgetSelect(value) {
  state.constraints.budget_preference = value;
  wizardError.value = "";
  queueAutoAdvance("budget");
}

function handleSocialSelect(value) {
  state.constraints.social_preference = value;
  wizardError.value = "";
  queueAutoAdvance("social");
}

function selectQuickTime(minutes) {
  timeMode.value = "quick";
  state.constraints.time_minutes = minutes;
  wizardError.value = "";
  queueAutoAdvance("time");
}

function selectCustomTime() {
  timeMode.value = "other";
  wizardError.value = "";

  if (quickTimeChoices.includes(Number(state.constraints.time_minutes))) {
    state.constraints.time_minutes = "";
  }
}

async function handleGenerateFromSurprise() {
  try {
    await generateSuggestion();
    setWizardStep(STEP_INDEX.result, "forward");
  } catch {
    // Error state is handled in shared state.
  }
}

watch(
  () => state.constraints.time_minutes,
  (value) => {
    if (value === "" || value === null || value === undefined) {
      return;
    }

    timeMode.value = quickTimeChoices.includes(Number(value)) ? "quick" : "other";
  },
  { immediate: true }
);

watch(
  () => [
    state.constraints.time_minutes,
    state.constraints.budget_preference,
    state.constraints.mood,
    state.constraints.social_preference,
    state.constraints.excluded_categories.join("|"),
  ],
  () => {
    resetGeneratedSuggestion();
    wizardError.value = "";
  }
);

watch(
  () => state.suggestion,
  (suggestion) => {
    if (!suggestion && wizardStepIndex.value === STEP_INDEX.result) {
      setWizardStep(STEP_INDEX.surprise, "backward");
    }
  }
);
</script>

<template>
  <section class="panel generator-form-card flow-panel">
    <div class="panel-heading">
      <h2>Random Activity</h2>
      <p>Step through your choices, then reveal one suggestion.</p>
    </div>

    <p v-if="state.formErrors.constraints._form" class="form-inline-error">
      {{ state.formErrors.constraints._form }}
    </p>

    <div class="wizard-progress-row">
      <span class="wizard-progress-label">Step {{ wizardProgress }}</span>
      <div class="wizard-dots">
        <button
          v-for="(step, index) in wizardSteps"
          :key="step.key"
          type="button"
          class="wizard-dot"
          :class="{ active: index === wizardStepIndex }"
          :aria-label="`Go to ${step.label}`"
          @click="jumpToStep(index)"
        />
      </div>
    </div>

    <Transition :name="stepTransitionName" mode="out-in">
      <article :key="currentWizardStep.key" class="wizard-card">
        <template v-if="currentWizardStep.key === 'mood'">
          <p class="section-kicker">1. Mood</p>
          <h3 class="wizard-question">How are you feeling today?</h3>
          <p class="wizard-note">Pick the vibe first. We tune the suggestion to this.</p>

          <div class="choice-chip-grid">
            <button
              v-for="mood in availableMoodOptions"
              :key="mood.value"
              type="button"
              class="choice-chip"
              :class="{ active: state.constraints.mood === mood.value }"
              :aria-pressed="state.constraints.mood === mood.value"
              @click="handleMoodSelect(mood.value)"
            >
              <span class="mood-copy">{{ mood.label }}</span>
            </button>
          </div>
        </template>

        <template v-else-if="currentWizardStep.key === 'time'">
          <p class="section-kicker">2. Time</p>
          <h3 class="wizard-question">How much time do you have?</h3>
          <p class="wizard-note">Choose a quick option or enter your own value.</p>

          <div class="time-choice-list">
            <button
              v-for="minutes in quickTimeChoices"
              :key="minutes"
              type="button"
              class="time-choice-chip"
              :class="{ active: isQuickTimeActive(minutes) && timeMode === 'quick' }"
              @click="selectQuickTime(minutes)"
            >
              {{ minutes }} min
            </button>
            <button
              type="button"
              class="time-choice-chip"
              :class="{ active: timeMode === 'other' }"
              @click="selectCustomTime"
            >
              Other...
            </button>
          </div>

          <input
            v-if="timeMode === 'other'"
            v-model.number="state.constraints.time_minutes"
            type="number"
            min="5"
            max="1440"
            step="5"
            placeholder="e.g. 45"
            class="time-other-input"
          />

          <div class="wizard-nav">
            <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
            <button type="button" class="primary-button" @click="goNextStep">Continue</button>
          </div>
        </template>

        <template v-else-if="currentWizardStep.key === 'budget'">
          <p class="section-kicker">3. Budget</p>
          <h3 class="wizard-question">What budget feels right?</h3>
          <p class="wizard-note">Use a tier instead of raw numbers for faster decisions.</p>

          <div class="choice-chip-grid">
            <button
              v-for="option in budgetOptions"
              :key="option.value"
              type="button"
              class="choice-chip"
              :class="{ active: state.constraints.budget_preference === option.value }"
              :aria-pressed="state.constraints.budget_preference === option.value"
              @click="handleBudgetSelect(option.value)"
            >
              <span class="mood-copy">{{ option.label }}</span>
            </button>
          </div>

          <div class="wizard-nav">
            <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
          </div>
        </template>

        <template v-else-if="currentWizardStep.key === 'social'">
          <p class="section-kicker">4. Social</p>
          <h3 class="wizard-question">Who is joining?</h3>
          <p class="wizard-note">We prioritize activities that fit this social mode.</p>

          <div class="choice-chip-grid">
            <button
              v-for="preference in availableSocialOptions"
              :key="preference.value"
              type="button"
              class="choice-chip"
              :class="{ active: state.constraints.social_preference === preference.value }"
              :aria-pressed="state.constraints.social_preference === preference.value"
              @click="handleSocialSelect(preference.value)"
            >
              <span class="mood-copy">{{ preference.label }}</span>
            </button>
          </div>

          <div class="wizard-nav">
            <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
          </div>
        </template>

        <template v-else-if="currentWizardStep.key === 'surprise'">
          <p class="section-kicker">5. Surprise</p>
          <h3 class="wizard-question">Ready for a surprise?</h3>
          <p class="wizard-note">
            We will pick one activity based on your choices. You can always reroll later.
          </p>

          <div class="wizard-summary">
            <div class="wizard-summary-pill">
              <strong>Mood</strong>
              <span>{{ selectedMoodLabel }}</span>
            </div>
            <div class="wizard-summary-pill">
              <strong>Time</strong>
              <span>{{ state.constraints.time_minutes || "Not set" }} min</span>
            </div>
            <div class="wizard-summary-pill">
              <strong>Budget</strong>
              <span>{{ selectedBudgetLabel }}</span>
            </div>
            <div class="wizard-summary-pill">
              <strong>Social</strong>
              <span>{{ selectedSocialLabel }}</span>
            </div>
          </div>

          <div class="field">
            <span>Optional excluded categories</span>
            <div class="tag-grid">
              <button
                v-for="category in excludeCategoryOptions"
                :key="category.key"
                type="button"
                class="tag-button"
                :class="{ active: isCategoryExcluded(category) }"
                @click="toggleCategoryGroup(category.rawValues)"
              >
                <span v-if="isCategoryExcluded(category)" class="exclude-mark" aria-hidden="true">
                  ❌
                </span>
                <CategoryIcon
                  :name="category.icon"
                  :src="category.iconSrc"
                  class="category-chip-icon"
                />
                <span>{{ category.label }}</span>
              </button>
            </div>
          </div>

          <p v-if="hasPendingAcceptedSuggestion" class="inline-hint">
            You already have one accepted activity in history. You can still generate another.
          </p>

          <button
            class="primary-button generate-button wizard-surprise-button"
            :disabled="!isLoggedIn || state.busy.generate"
            @click="handleGenerateFromSurprise"
          >
            {{ state.busy.generate ? "Generating activity..." : "✨ Surprise me" }}
          </button>

          <div class="wizard-nav">
            <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
          </div>
        </template>

        <template v-else>
          <p class="section-kicker">6. Result</p>
          <h3 class="wizard-question">Your suggestion</h3>
          <p class="wizard-note">Review it, then accept, save, or try another one.</p>

          <ResultCard embedded />

          <div class="wizard-nav">
            <button
              type="button"
              class="ghost-button"
              @click="setWizardStep(STEP_INDEX.surprise, 'backward')"
            >
              Adjust choices
            </button>
          </div>
        </template>
      </article>
    </Transition>

    <p v-if="wizardError" class="form-inline-error">{{ wizardError }}</p>
  </section>
</template>
