<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { requestPasswordReset } from "../api";

const router = useRouter();
const form = reactive({
  email: "",
});

const isSending = ref(false);
const emailError = ref(""); 

// Validation logic stays the same; only the trigger timing changed.
function validateEmail() {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  if (!form.email) {
    emailError.value = "Please enter your email address.";
    return false;
  }
  if (!emailRegex.test(form.email)) {
    emailError.value = "Please enter a valid email address (e.g., name@example.com).";
    return false;
  }
  
  emailError.value = ""; 
  return true;
}

async function submit() {
  if (!validateEmail()) return;
  
  isSending.value = true;
  
  try {
    const data = await requestPasswordReset(form.email);

    if (data.demo_link) {
      window.prompt(
        "[Demo Mode] Link generated. Please copy the link below and open it in a new window:",
        data.demo_link
      );
      console.log("Password Reset Link:", data.demo_link);
    }
    alert(
      data.message
      || "If an account with that email exists, a password reset link has been generated."
    );
    router.push("/login");
  } catch (error) {
    console.error(error);
    alert(
      error?.response?.data?.detail
      || error?.response?.data?.error
      || "Network request failed. Please check if the backend server is running."
    );
  } finally {
    isSending.value = false;
  }
}
</script>

<template>
  <section class="panel auth-panel wide-panel auth-form-card">
    <div class="panel-heading">
      <h2>Reset Password</h2>
      <p>Enter your email to receive a reset link.</p>
    </div>

    <form class="stack" @submit.prevent="submit" novalidate>
      <label class="field">
        <span>Email Address</span>
        <input
          v-model="form.email"
          type="email"
          autocomplete="email"
          @input="validateEmail" 
        />
        <span v-if="emailError" style="color: #d32f2f; font-size: 0.85rem; margin-top: 4px; display: block;">
          {{ emailError }}
        </span>
      </label>

      <button class="primary-button roll-day-button" :disabled="isSending" type="submit">
        <span class="roll-day-content">
          <span>{{ isSending ? "Sending..." : "Send Reset Link" }}</span>
        </span>
      </button>
    </form>
  </section>
</template>
