<script setup>
import { ChevronRight } from 'lucide-vue-next';

// items: [{ label, to? }]
defineProps({
  items: { type: Array, default: () => [] }
});
</script>

<template>
  <nav class="flex items-center gap-1.5 text-sm text-slate-500">
    <template v-for="(item, i) in items" :key="i">
      <ChevronRight v-if="i > 0" class="h-4 w-4 text-slate-300" />
      <RouterLink
        v-if="item.to && i < items.length - 1"
        :to="item.to"
        class="hover:text-primary-600"
      >
        {{ item.label }}
      </RouterLink>
      <span v-else :class="i === items.length - 1 ? 'font-medium text-ink' : ''">
        {{ item.label }}
      </span>
    </template>
  </nav>
</template>
