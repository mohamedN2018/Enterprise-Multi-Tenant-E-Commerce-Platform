<script setup>
import { computed, useAttrs } from 'vue';

defineOptions({ inheritAttrs: false });

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  id: { type: String, default: '' }
});
const emit = defineEmits(['update:modelValue']);
const attrs = useAttrs();

const fieldId = computed(() => props.id || `f-${Math.abs(String(props.label).length + props.type.length)}-${props.label?.toLowerCase().replace(/\s+/g, '-')}`);
</script>

<template>
  <div>
    <label v-if="label" :for="fieldId" class="label">{{ label }}</label>
    <input
      :id="fieldId"
      :type="type"
      :value="modelValue"
      v-bind="attrs"
      class="input"
      :class="error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/20' : ''"
      @input="emit('update:modelValue', $event.target.value)"
    />
    <p v-if="error" class="mt-1 text-xs text-rose-600">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-xs text-slate-400">{{ hint }}</p>
  </div>
</template>
