<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { CheckCircle2, Package, ArrowRight } from 'lucide-vue-next';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Spinner from '@/components/ui/Spinner.vue';
import PageHero from '@/components/ui/PageHero.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useCartStore } from '@/stores/cart';
import { shop } from '@/services/shop';

const route = useRoute();
const cart = useCartStore();

const order = ref(null);
const loading = ref(true);
const failed = ref(false);

const currency = computed(() => order.value?.currency || '');

onMounted(async () => {
  try {
    const res = await shop.order(cart.headers, route.params.id);
    order.value = res.data;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <PageHero :title="$t('order.confirmation')" :items="[{ label: $t('nav.account'), to: { name: 'account' } }, { label: $t('order.order') }]" />
    <div class="container py-10">
    <div v-if="loading" class="flex min-h-[40vh] items-center justify-center">
      <Spinner :size="28" :label="$t('order.loading')" />
    </div>

    <EmptyState v-else-if="failed || !order" :title="$t('order.notFound')" :message="$t('order.notFoundMsg')">
      <RouterLink :to="{ name: 'account' }" class="btn btn-primary btn-sm">{{ $t('order.goToOrders') }}</RouterLink>
    </EmptyState>

    <div v-else class="mx-auto max-w-2xl">
      <div class="card p-8 text-center">
        <span class="mx-auto grid h-16 w-16 place-items-center rounded-full bg-emerald-100 text-emerald-600">
          <CheckCircle2 class="h-9 w-9" />
        </span>
        <h1 class="mt-5 text-2xl font-bold">{{ $t('order.thankYou') }}</h1>
        <p class="mt-1 text-slate-500">{{ $t('order.placedPrefix') }} <span class="font-semibold text-ink">#{{ order.number }}</span> {{ $t('order.placedSuffix') }}</p>
        <div class="mt-3 flex justify-center"><StatusBadge :status="order.status" /></div>
      </div>

      <div class="card mt-6 p-6">
        <h2 class="flex items-center gap-2 font-semibold"><Package class="h-5 w-5 text-primary-600" /> {{ $t('order.details') }}</h2>
        <ul class="mt-4 divide-y divide-slate-100">
          <li v-for="item in order.items" :key="item.id" class="flex items-center justify-between py-3 text-sm">
            <span class="text-slate-700">{{ item.product_name }} <span class="text-slate-400">× {{ item.quantity }}</span></span>
            <span class="font-medium">{{ item.line_total }} {{ currency }}</span>
          </li>
        </ul>
        <dl class="mt-4 space-y-2 border-t border-slate-100 pt-4 text-sm">
          <div class="flex justify-between"><dt class="text-slate-500">{{ $t('common.subtotal') }}</dt><dd>{{ order.subtotal }} {{ currency }}</dd></div>
          <div v-if="Number(order.discount_total) > 0" class="flex justify-between text-emerald-600"><dt>{{ $t('common.discount') }}</dt><dd>−{{ order.discount_total }} {{ currency }}</dd></div>
          <div v-if="Number(order.tax_total) > 0" class="flex justify-between"><dt class="text-slate-500">{{ $t('order.tax') }}</dt><dd>{{ order.tax_total }} {{ currency }}</dd></div>
          <div v-if="Number(order.shipping_total) > 0" class="flex justify-between"><dt class="text-slate-500">{{ $t('order.shipping') }}</dt><dd>{{ order.shipping_total }} {{ currency }}</dd></div>
          <div class="flex justify-between border-t border-slate-100 pt-2 text-base font-bold"><dt>{{ $t('common.total') }}</dt><dd>{{ order.total }} {{ currency }}</dd></div>
        </dl>
      </div>

      <div class="mt-6 flex justify-center gap-3">
        <RouterLink :to="{ name: 'account' }" class="btn btn-outline">{{ $t('order.viewMyOrders') }}</RouterLink>
        <RouterLink :to="{ name: 'products' }" class="btn btn-primary">{{ $t('order.continueShopping') }} <ArrowRight class="h-4 w-4 rtl:rotate-180" /></RouterLink>
      </div>
    </div>
    </div>
  </div>
</template>
