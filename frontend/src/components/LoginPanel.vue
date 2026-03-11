<script setup>
import { nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";

import diceIcon from "../assets/auth/roll-dice.gif";
import thinkingBroIllustration from "../assets/auth/positive-thinking-bro.svg";
import { loginWithPassword, state } from "../state";

const router = useRouter();
const usernameInputRef = ref(null);
const isMobileViewport = ref(false);
const showMobileIntro = ref(false);
const form = reactive({
  username: "",
  password: "",
});

function syncViewportMode() {
  if (typeof window === "undefined") {
    return;
  }
  const mobile = window.innerWidth <= 760;
  const wasMobile = isMobileViewport.value;
  isMobileViewport.value = mobile;

  if (!mobile) {
    showMobileIntro.value = false;
    return;
  }

  if (!wasMobile && mobile && !state.sessionToken) {
    showMobileIntro.value = true;
  }
}

function openSignInForm() {
  showMobileIntro.value = false;
  nextTick(() => {
    usernameInputRef.value?.focus();
  });
}

onMounted(() => {
  syncViewportMode();
  if (isMobileViewport.value && !state.sessionToken) {
    showMobileIntro.value = true;
  }
  window.addEventListener("resize", syncViewportMode);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", syncViewportMode);
});

watch(
  () => state.sessionToken,
  async (token) => {
    if (token) {
      await router.push("/dashboard");
    }
  }
);

async function submit() {
  try {
    await loginWithPassword(form);
  } catch {
    // Error message is handled in global state.
  }
}
</script>

<template>
  <Transition name="mobile-auth-reveal" mode="out-in">
    <section
      v-if="showMobileIntro"
      key="mobile-intro"
      class="panel auth-panel wide-panel auth-form-card mobile-login-intro"
    >
      <div class="mobile-intro-preview">
        <div class="mobile-intro-art-wrap">
          <img :src="thinkingBroIllustration" alt="" class="mobile-intro-art" />
          <span class="mobile-intro-dice-pulse" aria-hidden="true">
            <img :src="diceIcon" alt="" />
          </span>
        </div>
        <div class="mobile-intro-copy">
          <p class="mobile-intro-kicker">Generator Preview</p>
          <h2>Random Activity</h2>
          <p>Roll one idea based on mood, time, and budget.</p>
        </div>
      </div>

      <button type="button" class="primary-button mobile-intro-cta" @click="openSignInForm">
        Continue to Sign in
      </button>
    </section>

    <section v-else key="login-form" class="panel auth-panel wide-panel auth-form-card">
      <div class="panel-heading">
        <h2>Sign in</h2>
        <p>Use your account to jump back in.</p>
      </div>

      <form class="stack" @submit.prevent="submit">
        <p v-if="state.formErrors.login._form" class="form-inline-error">
          {{ state.formErrors.login._form }}
        </p>

        <label class="field">
          <span>Username</span>
          <input
            ref="usernameInputRef"
            v-model="form.username"
            type="text"
            autocomplete="username"
            :class="{ 'invalid-input': state.formErrors.login.username }"
          />
          <small v-if="state.formErrors.login.username" class="field-error">
            {{ state.formErrors.login.username }}
          </small>
        </label>

        <label class="field">
          <span>Password</span>
          <input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            :class="{ 'invalid-input': state.formErrors.login.password }"
          />
          <small v-if="state.formErrors.login.password" class="field-error">
            {{ state.formErrors.login.password }}
          </small>
        </label>

        <div class="forgot-password-container">
          <router-link to="/forgot-password" class="forgot-password-link">
            Forget your password?
          </router-link>
        </div>
        <button class="primary-button roll-day-button" :disabled="state.busy.auth">
          <span class="roll-day-content">
            <img
              :src="diceIcon"
              alt=""
              class="roll-day-dice"
            />
            <span>{{ state.busy.auth ? "Rolling..." : "Roll my day" }}</span>
          </span>
        </button>
      </form>
    </section>
  </Transition>
</template>

<style scoped>
.mobile-login-intro {
  display: grid;
  gap: 16px;
}

.mobile-intro-preview {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) minmax(0, 1.2fr);
  gap: 12px;
  align-items: center;
}

.mobile-intro-art-wrap {
  position: relative;
  border-radius: 18px;
  border: 1px solid rgba(31, 47, 62, 0.14);
  background: linear-gradient(155deg, #f9fffd, #f2f9ff);
  padding: 10px;
}

.mobile-intro-art {
  width: 100%;
  height: auto;
  object-fit: contain;
  display: block;
}

.mobile-intro-dice-pulse {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 38px;
  height: 38px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(31, 47, 62, 0.16);
  box-shadow: 0 8px 18px rgba(20, 52, 66, 0.16);
  animation: dice-pulse 1.5s ease-in-out infinite;
}

.mobile-intro-dice-pulse img {
  width: 20px;
  height: 20px;
}

.mobile-intro-copy {
  min-width: 0;
}

.mobile-intro-kicker {
  margin: 0 0 6px;
  font-size: 0.76rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #9a5d28;
  font-weight: 700;
}

.mobile-intro-copy h2 {
  margin: 0;
  font-size: clamp(1.55rem, 6vw, 2rem);
  line-height: 1;
}

.mobile-intro-copy p {
  margin: 8px 0 0;
  color: #5c7281;
  font-size: 0.94rem;
}

.mobile-intro-cta {
  min-height: 52px;
}

.forgot-password-container {
  text-align: right;
  margin-top: -8px;
  margin-bottom: 8px;
}

.forgot-password-link {
  font-size: 0.85rem;
  color: #6b7280; 
  text-decoration: none; 
  transition: all 0.2s ease; 
}


.forgot-password-link:hover {
  color: #111827; 
  text-decoration: underline; 
}

.mobile-auth-reveal-enter-active,
.mobile-auth-reveal-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.mobile-auth-reveal-enter-from,
.mobile-auth-reveal-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@keyframes dice-pulse {
  0% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.08);
  }

  100% {
    transform: scale(1);
  }
}

@media (min-width: 761px) {
  .mobile-login-intro {
    display: none !important;
  }
}

@media (max-width: 420px) {
  .mobile-intro-preview {
    grid-template-columns: 1fr;
  }
}
</style>
