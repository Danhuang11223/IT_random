<script setup>
import { RouterLink } from "vue-router";

import LoginPanel from "../components/LoginPanel.vue";
</script>

<template>
  <main class="single-column">
    <LoginPanel />

    <section class="panel helper-panel">
      <div class="panel-heading">
        <h2>没有账号？</h2>
        <p>先创建一个账号，注册成功后会自动登录。</p>
      </div>

      <RouterLink class="primary-link" to="/register">前往注册</RouterLink>
    </section>
  </main>
</template>
