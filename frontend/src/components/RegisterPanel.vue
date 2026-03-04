<script setup>
import { reactive, watch } from "vue";
import { useRouter } from "vue-router";

import { registerAccount, state } from "../state";

const router = useRouter();
const form = reactive({
  username: "",
  email: "",
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
    await registerAccount(form);
  } catch {
    // Error message is handled in global state.
  }
}
</script>

<template>
  <section class="panel auth-panel wide-panel">
    <div class="panel-heading">
      <h2>注册</h2>
      <p>创建新账号后会自动登录并进入控制台。</p>
    </div>

    <form class="stack" @submit.prevent="submit">
      <p v-if="state.formErrors.register._form" class="form-inline-error">
        {{ state.formErrors.register._form }}
      </p>

      <label class="field">
        <span>用户名</span>
        <input
          v-model="form.username"
          type="text"
          autocomplete="username"
          :class="{ 'invalid-input': state.formErrors.register.username }"
        />
        <small v-if="state.formErrors.register.username" class="field-error">
          {{ state.formErrors.register.username }}
        </small>
      </label>

      <label class="field">
        <span>邮箱（可选）</span>
        <input
          v-model="form.email"
          type="email"
          autocomplete="email"
          :class="{ 'invalid-input': state.formErrors.register.email }"
        />
        <small v-if="state.formErrors.register.email" class="field-error">
          {{ state.formErrors.register.email }}
        </small>
      </label>

      <label class="field">
        <span>密码</span>
        <input
          v-model="form.password"
          type="password"
          autocomplete="new-password"
          :class="{ 'invalid-input': state.formErrors.register.password }"
        />
        <small v-if="state.formErrors.register.password" class="field-error">
          {{ state.formErrors.register.password }}
        </small>
      </label>

      <button class="primary-button" :disabled="state.busy.auth">
        {{ state.busy.auth ? "提交中..." : "注册并进入" }}
      </button>
    </form>
  </section>
</template>
