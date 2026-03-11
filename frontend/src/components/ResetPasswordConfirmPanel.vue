<script setup>
import { reactive, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { confirmPasswordReset } from "../api";

const router = useRouter();
const route = useRoute(); 
const form = reactive({
  new_password: "",
  confirm_password: "",
});

const errorMessage = ref("");
const isSubmitting = ref(false);

async function submit() {
  
  errorMessage.value = "";

 
  if (form.new_password !== form.confirm_password) {
    errorMessage.value = "Passwords do not match!";
    return;
  }

 
  if (form.new_password.length < 8) {
    errorMessage.value = "Password must be at least 8 characters.";
    return;
  }

  isSubmitting.value = true;
  try {
    const data = await confirmPasswordReset({
      uid: String(route.params.uid || ""),
      token: String(route.params.token || ""),
      new_password: form.new_password,
    });
    alert(data.message || "Password updated successfully! Please login.");
    router.push("/login");
  } catch (error) {
    const validationError = error?.response?.data?.new_password;
    if (Array.isArray(validationError) && validationError.length) {
      errorMessage.value = String(validationError[0]);
      return;
    }

    errorMessage.value = (
      error?.response?.data?.error
      || error?.response?.data?.detail
      || "Connection failed. Is the backend running?"
    );
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <section class="panel auth-panel wide-panel auth-form-card">
    <div class="panel-heading">
      <h2>Create New Password</h2>
      <p>Secure your account with a new password.</p>
    </div>

    <form class="stack" @submit.prevent="submit">
      <p v-if="errorMessage" class="form-inline-error">
        {{ errorMessage }}
      </p>

      <label class="field">
        <span>New Password</span>
        <input 
          v-model="form.new_password" 
          type="password" 
          placeholder="At least 8 characters"
          required 
        />
      </label>

      <label class="field">
        <span>Confirm New Password</span>
        <input 
          v-model="form.confirm_password" 
          type="password" 
          :class="{ 'invalid-input': form.confirm_password && form.new_password !== form.confirm_password }"
          placeholder="Repeat your password"
          required 
        />
        <small v-if="form.confirm_password && form.new_password !== form.confirm_password" class="field-error">
          Passwords do not match yet.
        </small>
      </label>

      <button class="primary-button roll-day-button" :disabled="isSubmitting">
        <span class="roll-day-content">
          <span>{{ isSubmitting ? "Saving..." : "Update Password" }}</span>
        </span>
      </button>
    </form>
  </section>
</template>
