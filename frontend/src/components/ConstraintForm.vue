<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";

import celebrateGif from "../assets/celebrate.gif";
import diceIcon from "../assets/dice-random.svg";
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
  { key: "summary", label: "Summary" }, 
  { key: "roll", label: "Roll" },       
  { key: "result", label: "Result" },   
];

const STEP_INDEX = {
  mood: 0,
  time: 1,
  budget: 2,
  social: 3,
  summary: 4,
  roll: 5,
  result: 6,
};

// --- Change: added a 10 min option ---
const quickTimeChoices = [5, 10, 15, 30, 60];
// ------------------------------

const wizardStepIndex = ref(0);
const wizardDirection = ref("forward");
const wizardError = ref("");
const timeMode = ref("quick");
const isRollingDice = ref(false);
const celebrateVisible = ref(false);
const touchGesture = ref(null);
let celebrateTimerId = null;

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
  () => `${wizardStepIndex.value + 1} of ${wizardSteps.length}`
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
  if (index < 0 || index >= wizardSteps.length) return;
  wizardDirection.value = direction;
  wizardStepIndex.value = index;
  wizardError.value = "";
}

function jumpToStep(index) {
  if (index === wizardStepIndex.value) return;
  setWizardStep(index, index > wizardStepIndex.value ? "forward" : "backward");
}

function goPreviousStep() {
  setWizardStep(wizardStepIndex.value - 1, "backward");
}

function goNextStep() {
  const stepKey = currentWizardStep.value.key;
  if (!isStepReady(stepKey)) {
    wizardError.value = stepErrorMessage(stepKey);
    return;
  }
  setWizardStep(wizardStepIndex.value + 1, "forward");
}

function handleSwipeLeft() {
  const stepKey = currentWizardStep.value.key;
  if (!["mood", "time", "budget", "social", "summary"].includes(stepKey)) return;
  if (!isStepReady(stepKey)) {
    wizardError.value = stepErrorMessage(stepKey);
    return;
  }
  goNextStep();
}

function handleSwipeRight() {
  if (currentWizardStep.value.key === "result") {
    setWizardStep(STEP_INDEX.roll, "backward");
    return;
  }
  if (wizardStepIndex.value > 0) goPreviousStep();
}

function handleCardTouchStart(event) {
  if (!event.touches || event.touches.length !== 1) {
    touchGesture.value = null;
    return;
  }
  const touch = event.touches[0];
  touchGesture.value = { x: touch.clientX, y: touch.clientY, time: Date.now() };
}

function handleCardTouchEnd(event) {
  if (!touchGesture.value || !event.changedTouches || !event.changedTouches.length) {
    touchGesture.value = null;
    return;
  }
  const endTouch = event.changedTouches[0];
  const deltaX = endTouch.clientX - touchGesture.value.x;
  const deltaY = endTouch.clientY - touchGesture.value.y;
  const durationMs = Date.now() - touchGesture.value.time;
  touchGesture.value = null;

  if (durationMs > 700 || Math.abs(deltaX) < 56 || Math.abs(deltaX) < Math.abs(deltaY) * 1.2) return;
  deltaX < 0 ? handleSwipeLeft() : handleSwipeRight();
}

function isValidTimeSelection() {
  const rawTimeValue = String(state.constraints.time_minutes ?? "").trim();
  if (!rawTimeValue) return false;
  const timeValue = Number(rawTimeValue);
  return Number.isInteger(timeValue) && timeValue >= 5 && timeValue <= 1440 && timeValue % 5 === 0;
}

function stepErrorMessage(stepKey) {
  if (stepKey === "mood") return "Pick one mood to continue.";
  if (stepKey === "time") return "Choose a time value in 5-minute increments.";
  if (stepKey === "budget") return "Pick a budget level to continue.";
  if (stepKey === "social") return "Select who is joining.";
  return "";
}

function isStepReady(stepKey) {
  if (stepKey === "mood") return Boolean(state.constraints.mood);
  if (stepKey === "time") return isValidTimeSelection();
  if (stepKey === "budget") return Boolean(state.constraints.budget_preference);
  if (stepKey === "social") return Boolean(state.constraints.social_preference);
  return true;
}

function queueAutoAdvance(expectedStepKey) {
  window.setTimeout(() => {
    if (currentWizardStep.value.key !== expectedStepKey) return;
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

function submitCustomTime() {
  if (currentWizardStep.value.key !== "time" || timeMode.value !== "other") return;
  goNextStep();
}

async function handleGenerateFromSurprise() {
  if (state.busy.generate || isRollingDice.value) return;
  isRollingDice.value = true;
  try {
    await generateSuggestion();
    celebrateVisible.value = true;
    if (celebrateTimerId) window.clearTimeout(celebrateTimerId);
    celebrateTimerId = window.setTimeout(() => {
      celebrateVisible.value = false;
      celebrateTimerId = null;
    }, 1600);
    setWizardStep(STEP_INDEX.result, "forward");
  } catch {
  } finally {
    isRollingDice.value = false;
  }
}

watch(() => state.constraints.time_minutes, (value) => {
  if (value === "" || value === null || value === undefined) return;
  timeMode.value = quickTimeChoices.includes(Number(value)) ? "quick" : "other";
}, { immediate: true });

watch(() => [
  state.constraints.time_minutes,
  state.constraints.budget_preference,
  state.constraints.mood,
  state.constraints.social_preference,
  state.constraints.excluded_categories.join("|"),
], () => {
  resetGeneratedSuggestion();
  wizardError.value = "";
});

watch(() => state.suggestion, (suggestion) => {
  if (!suggestion && wizardStepIndex.value === STEP_INDEX.result) {
    setWizardStep(STEP_INDEX.roll, "backward");
  }
});

onBeforeUnmount(() => {
  if (celebrateTimerId) {
    window.clearTimeout(celebrateTimerId);
    celebrateTimerId = null;
  }
});
</script>

<template>
  <section class="panel generator-form-card flow-panel">
    <Transition name="celebrate-pop">
      <div v-if="celebrateVisible" class="celebrate-overlay" aria-hidden="true">
        <img :src="celebrateGif" alt="" />
      </div>
    </Transition>

    <div class="panel-heading">
      <h2>Let's pick something fun</h2>
      <p>Answer a few quick questions,<br>then let the generator surprise you.</p>
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

    <div class="wizard-stage">
      <Transition :name="stepTransitionName" mode="out-in">
        <article
          :key="currentWizardStep.key"
          class="wizard-card"
          @touchstart.passive="handleCardTouchStart"
          @touchend.passive="handleCardTouchEnd"
        >
          <template v-if="currentWizardStep.key === 'mood'">
            <h3 class="wizard-question">How are you feeling today?</h3>
            <p class="wizard-note">Tell us the vibe.<br>We will match the activity to it.</p>
            <div class="choice-chip-grid mood-options-grid">
              <button
                v-for="mood in availableMoodOptions"
                :key="mood.value"
                type="button"
                class="choice-chip"
                :class="{ active: state.constraints.mood === mood.value }"
                @click="handleMoodSelect(mood.value)"
              >
                <span class="mood-copy">{{ mood.label }}</span>
              </button>
            </div>
          </template>

          <template v-else-if="currentWizardStep.key === 'time'">
            <h3 class="wizard-question">How much time do you have?</h3>
            <p class="wizard-note">Pick a quick option<br>or enter your own time.</p>

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
                Custom time
              </button>
            </div>

            <input
              v-if="timeMode === 'other'"
              v-model.number="state.constraints.time_minutes"
              type="number"
              min="5" max="1440" step="5"
              placeholder="e.g. 45"
              class="time-other-input"
              @keydown.enter.prevent="submitCustomTime"
            />

            <div class="wizard-nav">
              <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
              <button v-if="timeMode === 'other'" type="button" class="primary-button" @click="submitCustomTime">
                Continue
              </button>
            </div>
          </template>

          <template v-else-if="currentWizardStep.key === 'budget'">
            <h3 class="wizard-question">What budget feels right?</h3>
            <p class="wizard-note">Pick a budget that feels comfortable.</p>
            <div class="choice-chip-grid">
              <button
                v-for="option in budgetOptions"
                :key="option.value"
                type="button"
                class="choice-chip"
                :class="{ active: state.constraints.budget_preference === option.value }"
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
            <h3 class="wizard-question">Who is joining today?</h3>
            <p class="wizard-note">We will suggest activities that fit this.</p>
            <div class="choice-chip-grid">
              <button
                v-for="preference in availableSocialOptions"
                :key="preference.value"
                type="button"
                class="choice-chip"
                :class="{ active: state.constraints.social_preference === preference.value }"
                @click="handleSocialSelect(preference.value)"
              >
                <span class="mood-copy">{{ preference.label }}</span>
              </button>
            </div>
            <div class="wizard-nav">
              <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
            </div>
          </template>

          <template v-else-if="currentWizardStep.key === 'summary'">
            <h3 class="wizard-question">Confirm your settings</h3>
            <p class="wizard-note">Check your preferences below.</p>
            <div class="wizard-summary">
              <div class="wizard-summary-pill"><strong>Mood</strong> <span>{{ selectedMoodLabel }}</span></div>
              <div class="wizard-summary-pill"><strong>Time</strong> <span>{{ state.constraints.time_minutes || "Not set" }} min</span></div>
              <div class="wizard-summary-pill"><strong>Budget</strong> <span>{{ selectedBudgetLabel }}</span></div>
              <div class="wizard-summary-pill"><strong>Social</strong> <span>{{ selectedSocialLabel }}</span></div>
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
                  <span v-if="isCategoryExcluded(category)" class="exclude-mark" aria-hidden="true">❌</span>
                  <CategoryIcon :name="category.icon" :src="category.iconSrc" class="category-chip-icon" />
                  <span>{{ category.label }}</span>
                </button>
              </div>
            </div>
            <div class="wizard-nav">
              <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
              <button type="button" class="primary-button" @click="goNextStep">Looks good</button>
            </div>
          </template>

          <template v-else-if="currentWizardStep.key === 'roll'">
            <h3 class="wizard-question">Ready for a surprise?</h3>
            <p class="wizard-note">One tap, one fresh idea.</p>
            <article class="surprise-action-card" :class="{ rolling: isRollingDice || state.busy.generate }" style="margin-top: 2rem;">
              <div class="surprise-dice-wrap">
                <span class="surprise-dice-ring" />
                <img class="surprise-dice-icon" :src="diceIcon" alt="" />
              </div>
              <div class="surprise-action-copy">
                <strong>Roll a random pick</strong>
                <p>If it is not right, reroll in Result.</p>
              </div>
              <button
                class="primary-button generate-button wizard-surprise-button"
                :disabled="!isLoggedIn || state.busy.generate || isRollingDice"
                @click="handleGenerateFromSurprise"
              >
                {{ state.busy.generate || isRollingDice ? "Rolling..." : "✨ Surprise me" }}
              </button>
            </article>
            <div class="wizard-nav">
              <button type="button" class="ghost-button" @click="goPreviousStep">Back</button>
            </div>
          </template>

          <template v-else-if="currentWizardStep.key === 'result'">
            <h3 class="wizard-question">Your suggestion</h3>
            <ResultCard embedded />
            <div class="wizard-nav">
              <button type="button" class="ghost-button" @click="setWizardStep(STEP_INDEX.summary, 'backward')">Adjust choices</button>
            </div>
          </template>
        </article>
      </Transition>
    </div>
    <p v-if="wizardError" class="form-inline-error">{{ wizardError }}</p>
  </section>
</template>

<style scoped>
/* --- 1. Center time options and refine shape consistency --- */
.time-choice-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin: 1.5rem 0;
}

.time-other-input {
  display: block;
  margin: 1rem auto;
  text-align: center;
  max-width: 240px;
}

/* Force all time options except the last one (Custom time) to be perfect circles. */
.time-choice-list .time-choice-chip:not(:last-child) {
  width: 74px;
  height: 74px;
  padding: 0; 
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

/* Keep the last "Custom time" option in a pill shape. */
.time-choice-list .time-choice-chip:last-child {
  height: 74px;
  padding: 0 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 37px;
}


/* --- 2. Dice-specific animation only --- */
.surprise-dice-wrap {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto 1.5rem;
  display: flex !important;
  align-items: center;
  justify-content: center;
}

.surprise-dice-icon {
  display: block !important;
  width: 54px !important;
  height: 54px !important;
  z-index: 5;
  animation: dice-float-idle 2.5s ease-in-out infinite !important;
  filter: drop-shadow(0 5px 8px rgba(0,0,0,0.15));
}

.surprise-dice-ring {
  position: absolute;
  inset: 0;
  border: 2px dashed #00796b !important;
  border-radius: 50%;
  opacity: 0.4;
  animation: ring-spin-idle 10s linear infinite !important;
}

.rolling .surprise-dice-icon {
  animation: dice-active-jump 0.4s ease-in-out infinite !important;
}

.rolling .surprise-dice-ring {
  animation: ring-spin-fast 0.6s linear infinite !important;
  border-style: solid !important;
  border-color: #ffca28 !important;
  opacity: 1;
}

@keyframes dice-float-idle {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}
@keyframes ring-spin-idle {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes dice-active-jump {
  0%, 100% { transform: translateY(0) scale(1); }
  50% { transform: translateY(-6px) scale(1.08); }
}
@keyframes ring-spin-fast {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* --- 3. New: move the card question slightly downward --- */
.wizard-question {
  margin-top: 0.3rem;
}

/* --- 4. New: move the first card (Mood) options up and fix shrink/flatten behavior --- */
.mood-options-grid {
  width: 100% !important; 
  margin-top: 0.55rem !important;
  margin-bottom: auto !important; 
}

/* Restore button height and slightly reduce horizontal padding for label space. */
.mood-options-grid .choice-chip {
  min-height: 108px !important;
  padding-left: 0.5rem !important;  /* Reduce horizontal padding slightly. */
  padding-right: 0.5rem !important;
}

/* --- 5. New: force option text to remain on a single line --- */
.mood-options-grid .mood-copy {
  white-space: normal !important;
  text-align: center;
  line-height: 1.2;
}

@media (max-width: 560px) {
  .time-choice-list .time-choice-chip:not(:last-child) {
    width: 64px;
    height: 64px;
  }

  .time-choice-list .time-choice-chip:last-child {
    height: 64px;
    padding: 0 0.9rem;
    border-radius: 32px;
  }

  .mood-options-grid {
    margin-top: 0.35rem !important;
  }

  .mood-options-grid .choice-chip {
    min-height: 92px !important;
  }
}
</style>
