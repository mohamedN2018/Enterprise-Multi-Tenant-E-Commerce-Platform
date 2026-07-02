<script setup>
defineProps({
  size: { type: [Number, String], default: 20 },
  label: { type: String, default: '' }
});
</script>

<template>
  <span class="inline-flex items-center gap-2 text-slate-500">
    <svg
      class="animate-spin text-primary-600"
      :width="size"
      :height="size"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle class="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 0 1 8-8V0C5.4 0 0 5.4 0 12h4z"
      />
    </svg>
    <span v-if="label" class="text-sm">{{ label }}</span>
  </span>
</template>
