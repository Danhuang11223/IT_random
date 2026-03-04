<script setup>
import { RouterLink } from "vue-router";

import RegisterPanel from "../components/RegisterPanel.vue";
</script>

<template>
  <main class="single-column">
    <RegisterPanel />

    <section class="panel helper-panel">
      <div class="panel-heading">
        <h2>已经有账号？</h2>
        <p>直接登录即可进入控制台。</p>
      </div>

      <RouterLink class="primary-link" to="/login">返回登录</RouterLink>
    </section>
  </main>
</template>
