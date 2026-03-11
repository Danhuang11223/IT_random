<script setup>
import { RouterLink } from "vue-router";
import ResetPasswordConfirmPanel from "../components/ResetPasswordConfirmPanel.vue";
</script>

<template>
  <main class="single-column">
    <ResetPasswordConfirmPanel />
    <p class="auth-inline-row">
      Back to
      <RouterLink class="auth-inline-link" to="/login">Sign in</RouterLink>
    </p>
  </main>
</template>