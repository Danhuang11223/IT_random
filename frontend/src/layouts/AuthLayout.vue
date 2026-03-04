<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <section class="auth-layout">
    <aside class="auth-showcase">
      <p class="eyebrow">Daily Random Events</p>
      <h1>让今天有一个明确的开始</h1>
      <p class="showcase-copy">
        输入时间、预算和心情，系统帮你从可执行的活动池里抽出一个结果。
        不再卡在“待会儿再决定”。
      </p>

      <div class="showcase-points">
        <div class="showcase-chip">约束筛选</div>
        <div class="showcase-chip">随机生成</div>
        <div class="showcase-chip">完成记录</div>
      </div>

      <nav class="auth-nav">
        <RouterLink to="/login">登录</RouterLink>
        <RouterLink to="/register">注册</RouterLink>
      </nav>
    </aside>

    <div class="auth-stage">
      <RouterView />
    </div>
  </section>
</template>
