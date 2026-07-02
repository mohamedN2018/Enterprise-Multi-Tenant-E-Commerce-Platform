<script setup>
import { PackageOpen } from 'lucide-vue-next';

defineProps({
  icon: { type: [Object, Function], default: null },
  title: { type: String, default: 'Nothing here yet' },
  message: { type: String, default: '' }
});
</script>

<template>
  <div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/60 px-6 py-14 text-center">
    <component :is="icon || PackageOpen" class="mb-3 h-10 w-10 text-slate-300" />
    <h3 class="text-sm font-semibold text-ink">{{ title }}</h3>
    <p v-if="message" class="mt-1 max-w-sm text-sm text-slate-500">{{ message }}</p>
    <div v-if="$slots.default" class="mt-4">
      <slot />
    </div>
  </div>
</template>
