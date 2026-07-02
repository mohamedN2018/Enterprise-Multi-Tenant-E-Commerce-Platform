<script setup>
import { computed } from 'vue';
import { Info, CheckCircle2, AlertTriangle, XCircle } from 'lucide-vue-next';

const props = defineProps({
  variant: { type: String, default: 'info' }, // info | success | warning | error
  title: { type: String, default: '' }
});

const map = {
  info: { cls: 'border-sky-200 bg-sky-50 text-sky-800', icon: Info },
  success: { cls: 'border-emerald-200 bg-emerald-50 text-emerald-800', icon: CheckCircle2 },
  warning: { cls: 'border-amber-200 bg-amber-50 text-amber-800', icon: AlertTriangle },
  error: { cls: 'border-rose-200 bg-rose-50 text-rose-800', icon: XCircle }
};
const cfg = computed(() => map[props.variant] || map.info);
</script>

<template>
  <div class="flex items-start gap-3 rounded-lg border px-4 py-3 text-sm" :class="cfg.cls">
    <component :is="cfg.icon" class="mt-0.5 h-5 w-5 shrink-0" />
    <div class="flex-1">
      <p v-if="title" class="font-semibold">{{ title }}</p>
      <div class="leading-snug"><slot /></div>
    </div>
  </div>
</template>
