<script setup>
import { computed } from 'vue';
import { Star } from 'lucide-vue-next';

const props = defineProps({
  value: { type: Number, default: 0 },
  count: { type: Number, default: null },
  size: { type: Number, default: 16 },
  editable: { type: Boolean, default: false }
});
const emit = defineEmits(['update:value']);

const rounded = computed(() => Math.round(props.value));
const set = (n) => props.editable && emit('update:value', n);
</script>

<template>
  <div class="inline-flex items-center gap-1">
    <div class="flex" :class="editable ? 'cursor-pointer' : ''">
      <Star
        v-for="n in 5"
        :key="n"
        :size="size"
        class="transition-colors"
        :class="n <= rounded ? 'fill-amber-400 text-amber-400' : 'text-slate-300'"
        @click="set(n)"
      />
    </div>
    <span v-if="count !== null" class="text-xs font-medium text-slate-500">
      {{ Number(value).toFixed(1) }} <span class="text-slate-400">({{ count }})</span>
    </span>
  </div>
</template>
