<script setup>
import { RouterLink } from "vue-router";


import ForgotPasswordPanel from "../components/ForgotPasswordPanel.vue";
</script>

<template>
  <main class="single-column">
    <ForgotPasswordPanel />
    
    <p class="auth-inline-row">
      Remember your password?
      <RouterLink class="auth-inline-link" to="/login">Sign in</RouterLink>
    </p>
  </main>
</template>