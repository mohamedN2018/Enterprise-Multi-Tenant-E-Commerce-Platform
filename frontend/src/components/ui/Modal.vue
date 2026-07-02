<script setup>
import { watch, onBeforeUnmount } from 'vue';
import { X } from 'lucide-vue-next';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: { type: String, default: 'md' } // sm | md | lg | xl
});
const emit = defineEmits(['update:modelValue']);

const sizes = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl'
};

const close = () => emit('update:modelValue', false);
const onKey = (e) => e.key === 'Escape' && close();

watch(
  () => props.modelValue,
  (open) => {
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) window.addEventListener('keydown', onKey);
    else window.removeEventListener('keydown', onKey);
  }
);
onBeforeUnmount(() => {
  document.body.style.overflow = '';
  window.removeEventListener('keydown', onKey);
});
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/50 p-4 pt-[8vh] backdrop-blur-sm"
        @click.self="close"
      >
        <div class="w-full rounded-xl bg-white shadow-pop" :class="sizes[size] || sizes.md">
          <header
            v-if="title || $slots.header"
            class="flex items-center justify-between border-b border-slate-100 px-5 py-4"
          >
            <slot name="header">
              <h3 class="text-base font-semibold text-ink">{{ title }}</h3>
            </slot>
            <button class="text-slate-400 hover:text-slate-700" @click="close">
              <X class="h-5 w-5" />
            </button>
          </header>
          <div class="px-5 py-4">
            <slot />
          </div>
          <footer v-if="$slots.footer" class="border-t border-slate-100 px-5 py-4">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
