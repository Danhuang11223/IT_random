<script setup>
import { RouterLink } from "vue-router";

import RegisterPanel from "../components/RegisterPanel.vue";
</script>

<template>
  <main class="single-column">
    <RegisterPanel />
    <p class="auth-inline-row">
      Already have an account?
      <RouterLink class="auth-inline-link" to="/login">Sign in</RouterLink>
    </p>
  </main>
</template>
