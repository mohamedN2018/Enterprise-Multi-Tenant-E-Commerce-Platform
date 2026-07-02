<script setup>
import { computed } from 'vue';

const props = defineProps({
  status: { type: [String, Boolean], default: '' },
  label: { type: String, default: '' }
});

const tones = {
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  amber: 'bg-amber-50 text-amber-700 ring-amber-200',
  red: 'bg-rose-50 text-rose-700 ring-rose-200',
  blue: 'bg-sky-50 text-sky-700 ring-sky-200',
  indigo: 'bg-primary-50 text-primary-700 ring-primary-200',
  gray: 'bg-slate-100 text-slate-600 ring-slate-200'
};

const map = {
  active: 'green',
  published: 'green',
  paid: 'green',
  completed: 'green',
  delivered: 'green',
  approved: 'green',
  succeeded: 'green',
  true: 'green',
  pending: 'amber',
  processing: 'blue',
  shipped: 'blue',
  draft: 'gray',
  inactive: 'gray',
  archived: 'gray',
  false: 'gray',
  cancelled: 'red',
  canceled: 'red',
  failed: 'red',
  refunded: 'red',
  rejected: 'red',
  suspended: 'red'
};

const key = computed(() => String(props.status).toLowerCase());
const tone = computed(() => tones[map[key.value]] || tones.indigo);
const text = computed(() => props.label || String(props.status).replace(/_/g, ' '));
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ring-1 ring-inset"
    :class="tone"
  >
    {{ text }}
  </span>
</template>
