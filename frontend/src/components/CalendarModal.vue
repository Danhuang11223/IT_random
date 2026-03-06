<script setup>
import { computed, reactive, watch } from "vue";

import {
  buildCalendarEventPayload,
  buildGoogleCalendarUrl,
  downloadIcs,
} from "../calendar";

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  activity: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["update:modelValue"]);

const form = reactive({
  dateYear: "",
  dateMonth: "",
  dateDay: "",
  startHour: "",
  startMinute: "",
  durationMinutes: "",
});

const errors = reactive({
  date: "",
  time: "",
  durationMinutes: "",
  form: "",
});

const canShow = computed(() => props.modelValue && Boolean(props.activity));

function resetErrors() {
  errors.date = "";
  errors.time = "";
  errors.durationMinutes = "";
  errors.form = "";
}

function primeDefaults() {
  form.dateYear = "";
  form.dateMonth = "";
  form.dateDay = "";
  form.startHour = "";
  form.startMinute = "";
  form.durationMinutes = props.activity?.min_time_minutes
    ? String(props.activity.min_time_minutes)
    : "30";
  resetErrors();
}

function normalizeSegment(value, maxLength) {
  return String(value || "")
    .replace(/\D/g, "")
    .slice(0, maxLength);
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      primeDefaults();
    }
  }
);

watch(
  () => props.activity,
  () => {
    if (props.modelValue) {
      primeDefaults();
    }
  }
);

function closeModal() {
  emit("update:modelValue", false);
}

function validateForm() {
  resetErrors();
  const duration = Number.parseInt(String(form.durationMinutes || ""), 10);
  const yearRaw = normalizeSegment(form.dateYear, 4);
  const monthRaw = normalizeSegment(form.dateMonth, 2);
  const dayRaw = normalizeSegment(form.dateDay, 2);
  const hourRaw = normalizeSegment(form.startHour, 2);
  const minuteRaw = normalizeSegment(form.startMinute, 2);

  form.dateYear = yearRaw;
  form.dateMonth = monthRaw;
  form.dateDay = dayRaw;
  form.startHour = hourRaw;
  form.startMinute = minuteRaw;

  const year = Number.parseInt(yearRaw, 10);
  const month = Number.parseInt(monthRaw, 10);
  const day = Number.parseInt(dayRaw, 10);
  const hour = Number.parseInt(hourRaw, 10);
  const minute = Number.parseInt(minuteRaw, 10);

  if (
    yearRaw.length !== 4
    || !Number.isInteger(year)
    || year < 2000
    || year > 2100
    || monthRaw.length < 1
    || !Number.isInteger(month)
    || month < 1
    || month > 12
    || dayRaw.length < 1
    || !Number.isInteger(day)
    || day < 1
    || day > 31
  ) {
    errors.date = "Enter date as numbers: YYYY / MM / DD.";
  }

  if (
    hourRaw.length < 1
    || !Number.isInteger(hour)
    || hour < 0
    || hour > 23
    || minuteRaw.length < 1
    || !Number.isInteger(minute)
    || minute < 0
    || minute > 59
  ) {
    errors.time = "Enter time as numbers: HH / MM (24-hour).";
  }

  if (!Number.isInteger(duration) || duration <= 0) {
    errors.durationMinutes = "Duration must be a positive whole number.";
  } else if (duration > 1440) {
    errors.durationMinutes = "Duration must be 1440 minutes or less.";
  }

  if (errors.date || errors.time || errors.durationMinutes) {
    return null;
  }

  const dateValue = `${yearRaw}-${monthRaw.padStart(2, "0")}-${dayRaw.padStart(2, "0")}`;
  const timeValue = `${hourRaw.padStart(2, "0")}:${minuteRaw.padStart(2, "0")}`;

  try {
    return buildCalendarEventPayload(props.activity, {
      date: dateValue,
      startTime: timeValue,
      durationMinutes: duration,
    });
  } catch (error) {
    errors.form = error?.message || "Unable to create calendar event.";
    return null;
  }
}

function handleDownloadIcs() {
  const payload = validateForm();
  if (!payload) {
    return;
  }
  downloadIcs(payload);
}

function handleOpenGoogle() {
  const payload = validateForm();
  if (!payload) {
    return;
  }
  const url = buildGoogleCalendarUrl(payload);
  window.open(url, "_blank", "noopener,noreferrer");
}
</script>

<template>
  <teleport to="body">
    <div v-if="canShow" class="calendar-modal-overlay" @click.self="closeModal">
      <section
        class="calendar-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Add activity to calendar"
      >
        <header class="calendar-modal-header">
          <div>
            <h3>Add to Calendar</h3>
            <p>{{ props.activity?.title }}</p>
          </div>
          <button type="button" class="ghost-button small-button" @click="closeModal">
            Close
          </button>
        </header>

        <div class="calendar-modal-content">
          <label class="field">
            <span>Date (numbers only)</span>
            <div class="calendar-segment-row date-row">
              <input
                v-model="form.dateYear"
                type="text"
                inputmode="numeric"
                placeholder="YYYY"
                autocomplete="off"
                maxlength="4"
                class="segment-input segment-year"
                :class="{ 'invalid-input': errors.date }"
              />
              <span class="segment-separator">/</span>
              <input
                v-model="form.dateMonth"
                type="text"
                inputmode="numeric"
                placeholder="MM"
                autocomplete="off"
                maxlength="2"
                class="segment-input segment-month"
                :class="{ 'invalid-input': errors.date }"
              />
              <span class="segment-separator">/</span>
              <input
                v-model="form.dateDay"
                type="text"
                inputmode="numeric"
                placeholder="DD"
                autocomplete="off"
                maxlength="2"
                class="segment-input segment-day"
                :class="{ 'invalid-input': errors.date }"
              />
            </div>
            <small v-if="errors.date" class="field-error">{{ errors.date }}</small>
          </label>

          <label class="field">
            <span>Start time (numbers only)</span>
            <div class="calendar-segment-row time-row">
              <input
                v-model="form.startHour"
                type="text"
                inputmode="numeric"
                placeholder="HH"
                autocomplete="off"
                maxlength="2"
                class="segment-input segment-hour"
                :class="{ 'invalid-input': errors.time }"
              />
              <span class="segment-separator">:</span>
              <input
                v-model="form.startMinute"
                type="text"
                inputmode="numeric"
                placeholder="MM"
                autocomplete="off"
                maxlength="2"
                class="segment-input segment-minute"
                :class="{ 'invalid-input': errors.time }"
              />
            </div>
            <small v-if="errors.time" class="field-error">{{ errors.time }}</small>
          </label>

          <label class="field">
            <span>Duration (minutes)</span>
            <input
              v-model="form.durationMinutes"
              type="number"
              min="1"
              max="1440"
              step="1"
              :class="{ 'invalid-input': errors.durationMinutes }"
            />
            <small v-if="errors.durationMinutes" class="field-error">
              {{ errors.durationMinutes }}
            </small>
          </label>

          <p v-if="errors.form" class="form-inline-error">{{ errors.form }}</p>
        </div>

        <footer class="calendar-modal-actions">
          <button type="button" class="ghost-button" @click="handleDownloadIcs">
            Download .ics
          </button>
          <button type="button" class="primary-button" @click="handleOpenGoogle">
            Open Google Calendar
          </button>
        </footer>
      </section>
    </div>
  </teleport>
</template>
