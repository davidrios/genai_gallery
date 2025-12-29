<script setup lang="ts">
import { ref } from 'vue';
import { useIntersectionObserver } from '@vueuse/core';

const props = defineProps<{
  page: number;
}>();

const emit = defineEmits<{
  (e: 'visible', page: number): void;
}>();

const root = ref<HTMLElement | null>(null);

useIntersectionObserver(
  root,
  ([{ isIntersecting }]) => {
    if (isIntersecting) {
      emit('visible', props.page);
    }
  },
  { threshold: 0.1 }
);
</script>

<template>
  <div ref="root">
    <slot></slot>
  </div>
</template>
