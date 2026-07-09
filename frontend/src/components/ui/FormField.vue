<script setup>
import { computed, ref, useAttrs } from 'vue';
import { Eye, EyeOff } from 'lucide-vue-next';

defineOptions({ inheritAttrs: false });

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: '' },
  type: { type: String, default: 'text' },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  id: { type: String, default: '' },
  // Optional leading icon (a lucide component) for a clearer, friendlier field.
  icon: { type: [Object, Function], default: null }
});
const emit = defineEmits(['update:modelValue']);
const attrs = useAttrs();

const show = ref(false);
const isPassword = computed(() => props.type === 'password');
// A password field renders a show/hide toggle and swaps to text when revealed.
const inputType = computed(() => (isPassword.value && show.value ? 'text' : props.type));

const fieldId = computed(
  () => props.id || `f-${Math.abs(String(props.label).length + props.type.length)}-${props.label?.toLowerCase().replace(/\s+/g, '-')}`
);
</script>

<template>
  <div>
    <label v-if="label" :for="fieldId" class="label">{{ label }}</label>
    <div class="relative">
      <span
        v-if="icon"
        class="pointer-events-none absolute inset-y-0 start-0 grid w-10 place-items-center text-slate-400"
      >
        <component :is="icon" class="h-4 w-4" />
      </span>
      <input
        :id="fieldId"
        :type="inputType"
        :value="modelValue"
        v-bind="attrs"
        class="input"
        :class="[
          error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500/20' : '',
          icon ? 'ps-10' : '',
          isPassword ? 'pe-10' : ''
        ]"
        @input="emit('update:modelValue', $event.target.value)"
      />
      <button
        v-if="isPassword"
        type="button"
        tabindex="-1"
        class="absolute inset-y-0 end-0 grid w-10 place-items-center text-slate-400 transition hover:text-primary-600"
        :aria-label="show ? 'Hide password' : 'Show password'"
        @click="show = !show"
      >
        <component :is="show ? EyeOff : Eye" class="h-4 w-4" />
      </button>
    </div>
    <p v-if="error" class="mt-1 text-xs text-rose-600">{{ error }}</p>
    <p v-else-if="hint" class="mt-1 text-xs text-slate-400">{{ hint }}</p>
  </div>
</template>
