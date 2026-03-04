<script setup>
import { RouterLink } from "vue-router";

import LoginPanel from "../components/LoginPanel.vue";
</script>

<template>
  <main class="single-column">
    <LoginPanel />
    <p class="auth-inline-row">
      No account yet?
      <RouterLink class="auth-inline-link" to="/register">Create account</RouterLink>
    </p>
  </main>
</template>
