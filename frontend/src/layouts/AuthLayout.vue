<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>

<template>
  <section class="auth-layout">
    <aside class="auth-showcase">
      <p class="eyebrow">Daily Random Events</p>
      <h1>Not sure what to do today?</h1>
      <p class="showcase-copy">
        Generate a random activity based on your mood, time, and preferences.
      </p>
      <p class="showcase-note">No more "maybe later."</p>

      <div class="showcase-points">
        <div class="showcase-chip">Set limits</div>
        <div class="showcase-chip">Generate</div>
        <div class="showcase-chip">Track progress</div>
      </div>

      <nav class="auth-nav">
        <RouterLink class="auth-cta-primary" to="/login">Sign in</RouterLink>
        <RouterLink class="auth-cta-secondary" to="/register">Create account</RouterLink>
      </nav>
    </aside>

    <div class="auth-stage">
      <RouterView />
    </div>
  </section>
</template>
