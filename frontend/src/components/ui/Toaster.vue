<script setup>
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-vue-next';
import { useUiStore } from '@/stores/ui';

const ui = useUiStore();

const icons = { success: CheckCircle2, error: AlertCircle, info: Info };
const tones = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  error: 'border-rose-200 bg-rose-50 text-rose-800',
  info: 'border-slate-200 bg-white text-ink'
};
</script>

<template>
  <div class="fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2">
    <TransitionGroup name="toast">
      <div
        v-for="t in ui.toasts"
        :key="t.id"
        class="flex items-start gap-3 rounded-lg border px-4 py-3 shadow-pop"
        :class="tones[t.type] || tones.info"
      >
        <component :is="icons[t.type] || icons.info" class="mt-0.5 h-5 w-5 shrink-0" />
        <p class="flex-1 text-sm font-medium leading-snug">{{ t.message }}</p>
        <button class="opacity-60 hover:opacity-100" @click="ui.dismiss(t.id)">
          <X class="h-4 w-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(1rem);
}
</style>
