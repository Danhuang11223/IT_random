<script setup>
import { reactive, watch } from "vue";
import { useRouter } from "vue-router";

import { loginWithPassword, state } from "../state";

const router = useRouter();
const form = reactive({
  username: "admin",
  password: "Admin123456!",
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

      <button class="primary-button" :disabled="state.busy.auth">
        {{ state.busy.auth ? "Signing in..." : "Sign in" }}
      </button>
    </form>
  </section>
</template>
