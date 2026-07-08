<script setup>
import { computed } from 'vue';
import { Clock, CheckCircle2, Package, Truck, MapPin, Home, XCircle } from 'lucide-vue-next';
import { ORDER_STEPS, statusLabel } from '@/utils/orderStatus';

const props = defineProps({ order: { type: Object, required: true } });

const ICONS = {
  pending: Clock,
  confirmed: CheckCircle2,
  processing: Package,
  shipped: Truck,
  out_for_delivery: MapPin,
  delivered: Home
};

const events = computed(() => props.order?.events || []);
const eventAt = (status) => events.value.find((e) => e.status === status)?.created_at;
const cancelled = computed(() => ['cancelled', 'canceled', 'refunded'].includes(props.order?.status));
const currentIndex = computed(() => ORDER_STEPS.indexOf(props.order?.status));

const steps = computed(() =>
  ORDER_STEPS.map((s, i) => ({
    status: s,
    label: statusLabel(s),
    icon: ICONS[s],
    at: eventAt(s),
    done: currentIndex.value >= 0 && i < currentIndex.value,
    current: i === currentIndex.value
  }))
);
</script>

<template>
  <div>
    <div v-if="cancelled" class="flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2.5 text-sm font-semibold text-rose-700 dark:bg-rose-500/10">
      <XCircle class="h-5 w-5 shrink-0" /> {{ $t('status.cancelled') }}
    </div>
    <ol v-else class="relative">
      <li v-for="(step, i) in steps" :key="step.status" class="flex gap-3">
        <div class="flex flex-col items-center">
          <span
            class="grid h-9 w-9 shrink-0 place-items-center rounded-full border-2 transition"
            :class="step.done || step.current ? 'border-primary-600 bg-primary-600 text-white' : 'border-slate-200 bg-white text-slate-300 dark:border-slate-700 dark:bg-slate-800'"
          >
            <component :is="step.icon" class="h-4 w-4" />
          </span>
          <span v-if="i < steps.length - 1" class="my-1 w-0.5 flex-1" :class="step.done ? 'bg-primary-600' : 'bg-slate-200 dark:bg-slate-700'"></span>
        </div>
        <div class="min-w-0 flex-1 pb-5 pt-1">
          <p class="text-sm font-semibold" :class="step.done || step.current ? 'text-ink dark:text-white' : 'text-slate-400'">
            {{ step.label }}
            <span v-if="step.current" class="ms-1 text-xs font-medium text-primary-600">• {{ $t('orderTrack.current') }}</span>
          </p>
          <p v-if="step.at" class="text-xs text-muted">{{ (step.at || '').replace('T', ' ').slice(0, 16) }}</p>
        </div>
      </li>
    </ol>

    <div v-if="order.tracking_number || order.carrier" class="mt-2 rounded-lg border border-slate-200 bg-lightbg/50 p-3 text-sm dark:border-slate-700">
      <p v-if="order.carrier"><span class="text-muted">{{ $t('orderTrack.carrier') }}:</span> <span class="font-semibold">{{ order.carrier }}</span></p>
      <p v-if="order.tracking_number"><span class="text-muted">{{ $t('orderTrack.trackingNo') }}:</span> <span class="font-semibold">{{ order.tracking_number }}</span></p>
    </div>
  </div>
</template>
