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
  <section class="panel auth-panel wide-panel">
    <div class="panel-heading">
      <h2>登录</h2>
      <p>用已有账号进入控制台并生成随机事件。</p>
    </div>

    <form class="stack" @submit.prevent="submit">
      <p v-if="state.formErrors.login._form" class="form-inline-error">
        {{ state.formErrors.login._form }}
      </p>

      <label class="field">
        <span>用户名</span>
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
        <span>密码</span>
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
        {{ state.busy.auth ? "登录中..." : "登录" }}
      </button>
    </form>
  </section>
</template>
