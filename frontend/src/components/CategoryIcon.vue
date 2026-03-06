<script setup>
import { computed, ref, watch } from "vue";

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
  src: {
    type: String,
    default: "",
  },
});

const imageFailed = ref(false);
const imageSrc = computed(() => String(props.src || "").trim());
const showAnimatedImage = computed(() => Boolean(imageSrc.value) && !imageFailed.value);

watch(
  () => props.src,
  () => {
    imageFailed.value = false;
  }
);

function handleImageError() {
  imageFailed.value = true;
}
</script>

<template>
  <span class="category-icon-inner" aria-hidden="true">
    <img
      v-if="showAnimatedImage"
      :src="imageSrc"
      alt=""
      @error="handleImageError"
    />

    <svg
      v-else-if="name === 'stay-in'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M4 10.5L12 4l8 6.5" />
      <path d="M6 9.8V20h12V9.8" />
      <path d="M10 20v-5h4v5" />
    </svg>

    <svg
      v-else-if="name === 'good-food'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M4 11h16" />
      <path d="M4 11c0 4.4 3.6 8 8 8s8-3.6 8-8" />
      <path d="M8 8.5c0-1 .8-1.8 1.8-1.8" />
      <path d="M11.5 8.2c0-.9.7-1.7 1.6-1.7" />
      <path d="M15 8.8c0-1 .8-1.8 1.8-1.8" />
    </svg>

    <svg
      v-else-if="name === 'go-out'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle cx="12" cy="12" r="8.5" />
      <path d="M10 10l5-2-2 5-5 2 2-5z" />
      <circle cx="12" cy="12" r="0.8" />
    </svg>

    <svg
      v-else-if="name === 'get-inspired'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M12 4.2a4.8 4.8 0 0 1 4.8 4.8c0 1.5-.6 2.6-1.6 3.5-.7.6-1.1 1.2-1.1 2V15H9.9v-.5c0-.8-.4-1.5-1.1-2.1C7.8 11.6 7.2 10.5 7.2 9A4.8 4.8 0 0 1 12 4.2z" />
      <path d="M10.1 17h3.8" />
      <path d="M10.8 19.5h2.4" />
      <path d="M3.6 18.8h7.1c1.4 0 2.7-.5 3.8-1.3l2.3-1.8c.8-.6 1.9-.5 2.4.3" />
    </svg>

    <svg
      v-else-if="name === 'stay-active'"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <circle cx="11.3" cy="5.8" r="1.8" />
      <path d="M11.3 7.8v4.9" />
      <path d="M11.3 10.7l-3.2 2.2" />
      <path d="M11.3 10.7l3.4 2.2" />
      <path d="M11.3 12.7l-2.4 4.6" />
      <path d="M11.3 12.7l3.2 4.8" />
      <path d="M3 10.8h3.7" />
      <path d="M3 9.2v3.2" />
      <path d="M17.3 10.8H21" />
      <path d="M21 9.2v3.2" />
    </svg>
  </span>
</template>
