<script setup>
import { computed } from 'vue';
import { ChevronLeft, ChevronRight } from 'lucide-vue-next';

const props = defineProps({
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  total: { type: Number, default: 0 }
});
const emit = defineEmits(['update:page']);

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));
const from = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.pageSize + 1));
const to = computed(() => Math.min(props.page * props.pageSize, props.total));

const window = computed(() => {
  const last = pages.value;
  const cur = props.page;
  const out = [];
  const push = (n) => out.push(n);
  push(1);
  const start = Math.max(2, cur - 1);
  const end = Math.min(last - 1, cur + 1);
  if (start > 2) out.push('…');
  for (let i = start; i <= end; i += 1) push(i);
  if (end < last - 1) out.push('…');
  if (last > 1) push(last);
  return out;
});

const go = (n) => {
  if (n < 1 || n > pages.value || n === props.page) return;
  emit('update:page', n);
};
</script>

<template>
  <div class="flex flex-col items-center justify-between gap-3 sm:flex-row">
    <p class="text-sm text-slate-500">
      Showing <span class="font-medium text-ink">{{ from }}</span>–<span class="font-medium text-ink">{{ to }}</span>
      of <span class="font-medium text-ink">{{ total }}</span>
    </p>
    <nav class="flex items-center gap-1">
      <button class="btn btn-light btn-sm" :disabled="page <= 1" @click="go(page - 1)">
        <ChevronLeft class="h-4 w-4" />
      </button>
      <template v-for="(p, i) in window" :key="i">
        <span v-if="p === '…'" class="px-2 text-slate-400">…</span>
        <button
          v-else
          class="btn btn-sm min-w-9"
          :class="p === page ? 'btn-primary' : 'btn-light'"
          @click="go(p)"
        >
          {{ p }}
        </button>
      </template>
      <button class="btn btn-light btn-sm" :disabled="page >= pages" @click="go(page + 1)">
        <ChevronRight class="h-4 w-4" />
      </button>
    </nav>
  </div>
</template>
