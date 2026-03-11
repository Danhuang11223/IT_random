<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterView, useRoute } from "vue-router";

const route = useRoute();
const isMobileViewport = ref(false);

function syncViewportMode() {
  if (typeof window === "undefined") {
    return;
  }
  isMobileViewport.value = window.innerWidth <= 760;
}

onMounted(() => {
  syncViewportMode();
  window.addEventListener("resize", syncViewportMode);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", syncViewportMode);
});

const disableScaleForMobileAuth = computed(
  () =>
    isMobileViewport.value &&
    (route.name === "login" ||
      route.name === "register" ||
      route.name === "forgotPassword" ||
      route.name === "resetPasswordConfirm")
);
</script>

<template>
  <div class="root-shell">
    <div class="bg-decor">
      <img src="/decor/heart.svg" class="bg-icon i1" alt="" />
      <img src="/decor/mug.svg" class="bg-icon i2" alt="" />
      <img src="/decor/headphones.svg" class="bg-icon i3" alt="" />
      <img src="/decor/glass.svg" class="bg-icon i4" alt="" />
      <img src="/decor/reddit.svg" class="bg-icon i5" alt="" />
      <img src="/decor/awesome.svg" class="bg-icon i6" alt="" />
      <img src="/decor/fan.svg" class="bg-icon i7" alt="" />
      <img src="/decor/cat.svg" class="bg-icon i8" alt="" />
      <img src="/decor/emoji.svg" class="bg-icon i9" alt="" />
    </div>

    <div class="desktop-scale-shell" :class="{ 'no-app-scale': disableScaleForMobileAuth }">
      <RouterView />
    </div>
  </div>
</template>
