<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const form = reactive({
  email: "",
});

const isSending = ref(false);

async function submit() {
  isSending.value = true;
  try {
    
    const response = await fetch('http://127.0.0.1:8000/api/auth/password-reset/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.email })
    });

    const data = await response.json();

    if (response.ok) {
     
      window.prompt(
        "【Demo 演示模式】链接已生成，请直接复制下方链接，并在新窗口打开：", 
        data.demo_link
      );
      
      console.log("Password Reset Link:", data.demo_link);

      
      router.push("/login"); 
    } else {
      alert(`错误: ${data.error || '该邮箱不存在'}`);
    }
  } catch (error) {
    console.error(error);
    alert("网络请求失败，请检查 Django 后端是否正在运行？");
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

    <form class="stack" @submit.prevent="submit">
      <label class="field">
        <span>Email Address</span>
        <input
          v-model="form.email"
          type="email"
          autocomplete="email"
          required
        />
      </label>

      <button class="primary-button roll-day-button" :disabled="isSending" type="submit">
        <span class="roll-day-content">
          <span>{{ isSending ? "Sending..." : "Send Reset Link" }}</span>
        </span>
      </button>
    </form>
  </section>
</template>