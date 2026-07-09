<script setup>
import { computed } from 'vue';
import { Check, X } from 'lucide-vue-next';
import { t } from '@/i18n';

const props = defineProps({ value: { type: String, default: '' } });

// Requirement checklist (mirrors the backend's Django password validators).
const checks = computed(() => {
  const v = props.value || '';
  return [
    { key: 'len', ok: v.length >= 8, label: t('auth.pwReqLen') },
    { key: 'case', ok: /[a-z]/.test(v) && /[A-Z]/.test(v), label: t('auth.pwReqCase') },
    { key: 'num', ok: /\d/.test(v), label: t('auth.pwReqNum') },
    { key: 'sym', ok: /[^A-Za-z0-9]/.test(v), label: t('auth.pwReqSym') }
  ];
});
const score = computed(() => checks.value.filter((c) => c.ok).length);
const label = computed(() => ['', t('auth.pwWeak'), t('auth.pwFair'), t('auth.pwGood'), t('auth.pwStrong')][score.value]);
const barColor = computed(() =>
  ['bg-slate-200', 'bg-rose-500', 'bg-amber-500', 'bg-sky-500', 'bg-emerald-500'][score.value]
);
const textColor = computed(() =>
  score.value >= 3 ? 'text-emerald-600' : score.value >= 2 ? 'text-amber-600' : 'text-rose-600'
);
</script>

<template>
  <div v-if="value" class="mt-2">
    <div class="flex gap-1" role="progressbar" :aria-valuenow="score" aria-valuemin="0" aria-valuemax="4">
      <span
        v-for="i in 4"
        :key="i"
        class="h-1.5 flex-1 rounded-full transition-colors"
        :class="i <= score ? barColor : 'bg-slate-200 dark:bg-slate-700'"
      ></span>
    </div>
    <p class="mt-1 text-xs font-medium" :class="textColor">{{ label }}</p>
    <ul class="mt-1.5 grid grid-cols-2 gap-x-3 gap-y-1">
      <li
        v-for="c in checks"
        :key="c.key"
        class="flex items-center gap-1 text-xs"
        :class="c.ok ? 'text-emerald-600' : 'text-slate-400'"
      >
        <component :is="c.ok ? Check : X" class="h-3 w-3 shrink-0" /> {{ c.label }}
      </li>
    </ul>
  </div>
</template>
