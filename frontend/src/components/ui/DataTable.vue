<script setup>
import EmptyState from './EmptyState.vue';

// columns: [{ key, label, align?, width?, class? }]
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
              :class="[col.align === 'right' ? 'text-right' : '', col.class]"
              :style="col.width ? { width: col.width } : null"
            >
              {{ col.label }}
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
              v-for="row in rows"
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
