<script setup>
import { ref, computed } from 'vue';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-vue-next';
import EmptyState from './EmptyState.vue';

// columns: [{ key, label, align?, width?, class?, sortable? }]
// Use named slots `cell-<key>` (scope: { row, value }) for custom rendering.
const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, default: 'id' },
  loading: { type: Boolean, default: false },
  emptyTitle: { type: String, default: 'No records found' },
  emptyMessage: { type: String, default: '' },
  clickable: { type: Boolean, default: false }
});
const emit = defineEmits(['row-click']);

const value = (row, key) => key.split('.').reduce((o, k) => (o == null ? o : o[k]), row);

// Client-side sort of the currently loaded rows.
const sortKey = ref('');
const sortDir = ref('asc');

const toggleSort = (col) => {
  if (!col.sortable) return;
  if (sortKey.value === col.key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = col.key;
    sortDir.value = 'asc';
  }
};

const displayRows = computed(() => {
  if (!sortKey.value) return props.rows;
  const dir = sortDir.value === 'asc' ? 1 : -1;
  return [...props.rows].sort((a, b) => {
    const av = value(a, sortKey.value);
    const bv = value(b, sortKey.value);
    const an = Number(av);
    const bn = Number(bv);
    const numeric = av !== '' && bv !== '' && !Number.isNaN(an) && !Number.isNaN(bn);
    if (numeric) return (an - bn) * dir;
    return String(av ?? '').localeCompare(String(bv ?? '')) * dir;
  });
});
</script>

<template>
  <div class="card overflow-hidden p-0">
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-slate-100 bg-slate-50/70 text-left text-xs uppercase tracking-wide text-slate-500">
            <th
              v-for="col in columns"
              :key="col.key"
              class="whitespace-nowrap px-4 py-3 font-semibold"
              :class="[col.align === 'right' ? 'text-right' : '', col.class, col.sortable ? 'cursor-pointer select-none hover:text-ink' : '']"
              :style="col.width ? { width: col.width } : null"
              @click="toggleSort(col)"
            >
              <span class="inline-flex items-center gap-1" :class="col.align === 'right' ? 'flex-row-reverse' : ''">
                {{ col.label }}
                <template v-if="col.sortable">
                  <ChevronUp v-if="sortKey === col.key && sortDir === 'asc'" class="h-3.5 w-3.5 text-primary-600" />
                  <ChevronDown v-else-if="sortKey === col.key && sortDir === 'desc'" class="h-3.5 w-3.5 text-primary-600" />
                  <ChevronsUpDown v-else class="h-3.5 w-3.5 text-slate-300" />
                </template>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="`s-${n}`" class="border-b border-slate-50">
              <td v-for="col in columns" :key="col.key" class="px-4 py-3">
                <div class="skeleton h-4 w-full rounded"></div>
              </td>
            </tr>
          </template>
          <template v-else>
            <tr
              v-for="row in displayRows"
              :key="row[rowKey]"
              class="border-b border-slate-50 last:border-0"
              :class="clickable ? 'cursor-pointer hover:bg-slate-50/70' : ''"
              @click="clickable && emit('row-click', row)"
            >
              <td
                v-for="col in columns"
                :key="col.key"
                class="px-4 py-3 align-middle"
                :class="[col.align === 'right' ? 'text-right' : '', col.cellClass]"
              >
                <slot :name="`cell-${col.key}`" :row="row" :value="value(row, col.key)">
                  {{ value(row, col.key) ?? '—' }}
                </slot>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <div v-if="!loading && !rows.length" class="p-4">
      <EmptyState :title="emptyTitle" :message="emptyMessage" />
    </div>
  </div>
</template>
