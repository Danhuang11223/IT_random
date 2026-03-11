<script setup>
import { RouterView } from "vue-router";

import thinkingBroIllustration from "../assets/auth/positive-thinking-bro.svg";
</script>

<template>
  <section class="auth-layout auth-chat-layout">
    <div class="auth-chat-shell">
      <aside class="auth-chat-hero">
        <img
          class="hero-main-illustration"
          :src="thinkingBroIllustration"
          alt="Positive thinking illustration"
        />

        <div class="hero-copy-block">
          <p class="eyebrow">Daily Random Events</p>
          <h1>Not sure what to do today?</h1>
          <p class="hero-lead">Let randomness decide your day.</p>
          <p class="hero-subcopy">Generate activities based on mood and time.</p>
        </div>

        <div class="hero-chip-row">
          <span class="hero-chip">
            <span class="hero-chip-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <rect x="4.5" y="4.5" width="15" height="15" rx="3.5" />
                <circle cx="9" cy="9" r="1.1" />
                <circle cx="15" cy="9" r="1.1" />
                <circle cx="9" cy="15" r="1.1" />
                <circle cx="15" cy="15" r="1.1" />
              </svg>
            </span>
            <span>Generate activities</span>
          </span>
          <span class="hero-chip">
            <span class="hero-chip-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="8" />
                <path d="M12 7.5v5.1l3.2 1.8" />
              </svg>
            </span>
            <span>Based on mood &amp; time</span>
          </span>
          <span class="hero-chip">
            <span class="hero-chip-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="M4 19.2h16" />
                <rect x="6.1" y="11.3" width="2.6" height="5.9" rx="0.8" />
                <rect x="10.7" y="8.6" width="2.6" height="8.6" rx="0.8" />
                <rect x="15.3" y="6.2" width="2.6" height="11" rx="0.8" />
              </svg>
            </span>
            <span>Track your progress</span>
          </span>
        </div>
      </aside>

      <div class="auth-stage auth-chat-stage">
        <div class="auth-chat-form-wrap">
          <RouterView />
        </div>
      </div>
    </div>
  </section>
</template>
