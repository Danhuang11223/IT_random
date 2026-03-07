<script setup>
import { reactive, watch } from "vue";
import { useRouter } from "vue-router";

import diceIcon from "../assets/auth/roll-dice.gif";
import { loginWithPassword, state } from "../state";

const router = useRouter();
const form = reactive({
  username: "",
  password: "",
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
  <section class="panel auth-panel wide-panel auth-form-card">
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
</template>
