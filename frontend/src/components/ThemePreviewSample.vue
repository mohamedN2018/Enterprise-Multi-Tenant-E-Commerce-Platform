<script setup>
// A compact but complete sample of the live theme — header, product, prices,
// buttons, chips and status colours. Reused for the light and dark preview panes
// on the Appearance page (colours come from the brand CSS variables).
import { ShoppingCart, Star, Heart } from 'lucide-vue-next';
</script>

<template>
  <div class="space-y-3 bg-lightbg p-4">
    <div class="rounded-xl border border-slate-200 bg-white p-3">
      <div class="flex items-center justify-between">
        <span class="font-heading font-bold text-ink">{{ $t('appearance.sampleProduct') }}</span>
        <span class="font-heading text-lg font-extrabold text-primary-600">250 EGP</span>
      </div>
      <div class="mt-1 flex text-primary-600"><Star v-for="n in 5" :key="n" class="h-3.5 w-3.5 fill-primary-600" /></div>
      <div class="mt-3 flex gap-2">
        <button class="btn btn-primary btn-sm flex-1"><ShoppingCart class="h-4 w-4" /> {{ $t('product.addToCart') }}</button>
        <button class="grid h-8 w-8 place-items-center rounded-full border border-slate-200 text-primary-600 dark:border-slate-600"><Heart class="h-4 w-4" /></button>
      </div>
    </div>
    <div class="flex flex-wrap gap-1.5">
      <span class="chip border-0 bg-primary-50 text-primary-700">{{ $t('appearance.tagPrimary') }}</span>
      <span class="chip border-0 bg-secondary-500 text-white">{{ $t('appearance.tagSale') }}</span>
      <span class="chip border-0 bg-emerald-50 text-emerald-700">{{ $t('appearance.tagSuccess') }}</span>
      <span class="chip border-0 bg-amber-50 text-amber-700">{{ $t('appearance.tagPending') }}</span>
      <span class="chip border-0 bg-rose-50 text-rose-700">{{ $t('appearance.tagDanger') }}</span>
    </div>
    <div class="flex gap-2">
      <button class="btn btn-secondary btn-sm flex-1">{{ $t('appearance.tagSale') }}</button>
      <button class="btn btn-outline btn-sm flex-1">{{ $t('common.cancel') }}</button>
    </div>
  </div>
</template>
