<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
});
</script>

<template>
  <div class="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-2xl font-bold text-ink">{{ title }}</h1>
      <p v-if="subtitle" class="mt-0.5 text-sm text-slate-500">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="flex flex-wrap items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
