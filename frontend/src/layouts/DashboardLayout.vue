<script setup>
import { computed } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";

import { logout, state } from "../state";

const router = useRouter();

const nextStep = computed(() =>
  state.suggestion?.activity?.title
    ? state.suggestion.activity.title
    : state.pendingLog?.activity?.title
      ? state.pendingLog.activity.title
      : "还没有当前建议"
);
const flowStatus = computed(() => {
  if (state.pendingLog || state.suggestion?.is_accepted) {
    return "待记录";
  }

  if (state.suggestion) {
    return "待接受";
  }

  return "未开始";
});

function handleLogout() {
  logout();
  router.push("/login");
}
</script>

<template>
  <section class="dashboard-layout">
    <header class="dashboard-header">
      <div class="dashboard-header-copy">
        <p class="eyebrow">Decision Support</p>
        <h1>随机活动流程</h1>
        <p class="dashboard-subcopy">
          先输入约束，在当前页确认一个建议；接受后，再去历史记录页标记完成或跳过。
        </p>
      </div>

      <div class="dashboard-header-side">
        <nav class="nav-links">
          <RouterLink to="/dashboard">生成面板</RouterLink>
          <RouterLink to="/history">活动历史</RouterLink>
        </nav>

        <div class="user-badge">
          <span>{{ state.user?.username || "已登录用户" }}</span>
          <button class="ghost-button" @click="handleLogout">退出</button>
        </div>
      </div>
    </header>

    <section class="dashboard-summary">
      <div class="summary-card">
        <span>历史记录（当前筛选）</span>
        <strong>{{ state.pagination.count }}</strong>
      </div>
      <div class="summary-card">
        <span>当前建议</span>
        <strong>{{ nextStep }}</strong>
      </div>
      <div class="summary-card">
        <span>流程状态</span>
        <strong>{{ flowStatus }}</strong>
      </div>
    </section>

    <div class="dashboard-stage">
      <RouterView />
    </div>
  </section>
</template>
