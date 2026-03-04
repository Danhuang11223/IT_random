<script setup>
import { computed } from "vue";
import { RouterLink } from "vue-router";

import { getCategoryOption } from "../categoryOptions";
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
</script>

<template>
  <section class="panel result-panel">
    <div class="panel-heading">
      <h2>结果展示</h2>
      <p>这里展示你刚生成的活动。确认接受，或直接重抽一个新结果。</p>
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
              {{ state.suggestion.is_accepted ? "已接受" : "待确认" }}
            </span>
          </div>

          <h3>{{ state.suggestion.activity.title }}</h3>
          <p class="result-copy">{{ state.suggestion.activity.description }}</p>
          <p
            v-if="state.suggestion.fallback_applied && state.suggestion.fallback_message"
            class="inline-hint"
          >
            {{ state.suggestion.fallback_message }}
          </p>

          <dl class="metrics">
            <div>
              <dt>预计时长</dt>
              <dd>
                {{ state.suggestion.activity.min_time_minutes }} -
                {{ state.suggestion.activity.max_time_minutes }} 分钟
              </dd>
            </div>
            <div>
              <dt>预计预算</dt>
              <dd>{{ formatBudgetRange(state.suggestion.activity) }}</dd>
            </div>
            <div>
              <dt>社交类型</dt>
              <dd>{{ state.suggestion.activity.social_type }}</dd>
            </div>
          </dl>

          <div v-if="!state.suggestion.is_accepted" class="button-row">
            <button
              class="ghost-button"
              :disabled="rerollButtonDisabled"
              @click="handleReroll"
            >
              {{ state.busy.generate ? "重抽中..." : "重抽" }}
            </button>

            <button
              class="primary-button"
              :disabled="acceptButtonDisabled"
              @click="handleAccept"
            >
              {{ state.busy.accept ? "处理中..." : "接受" }}
            </button>
          </div>

          <div v-else class="accepted-guidance" role="status">
            <strong>下一步</strong>
            <p>活动已经确认。去历史记录页把它标记为“完成”或“跳过”。</p>
            <RouterLink class="primary-link" to="/history">前往历史记录</RouterLink>
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
        <p>你已经有一个已接受的活动待记录。先去历史记录页标记完成或跳过。</p>
        <RouterLink class="primary-link" to="/history">前往历史记录</RouterLink>
      </div>

      <div v-else key="result-empty" class="empty-state">
        <p>还没有生成结果。先填写左侧约束，再点击“✨ Surprise me”。</p>
      </div>
    </Transition>
  </section>
</template>
