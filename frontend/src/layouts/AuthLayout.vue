<script setup>
import { ShieldCheck, Store, TrendingUp } from 'lucide-vue-next';

const perks = [
  { icon: Store, title: 'Launch your storefront', text: 'Spin up a branded store in minutes.' },
  { icon: TrendingUp, title: 'Grow with insights', text: 'Rich analytics on every order.' },
  { icon: ShieldCheck, title: 'Enterprise-grade', text: 'Secure, multi-tenant, and reliable.' }
];
</script>

<template>
  <div class="grid min-h-screen lg:grid-cols-2">
    <div class="relative hidden overflow-hidden bg-primary-700 p-12 text-white lg:flex lg:flex-col">
      <div class="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary-500/40 blur-3xl"></div>
      <div class="absolute -bottom-24 -left-16 h-72 w-72 rounded-full bg-primary-400/30 blur-3xl"></div>
      <RouterLink :to="{ name: 'home' }" class="relative flex items-center gap-2 text-xl font-bold">
        <span class="grid h-10 w-10 place-items-center rounded-xl bg-white/15">
          <Store class="h-5 w-5" />
        </span>
        Marketplace
      </RouterLink>
      <div class="relative my-auto max-w-md">
        <h1 class="text-3xl font-bold leading-tight">Sell more with a platform built for scale.</h1>
        <p class="mt-3 text-primary-100">
          Everything you need to run a modern commerce business — catalog, inventory, checkout,
          payments and promotions.
        </p>
        <ul class="mt-8 space-y-5">
          <li v-for="p in perks" :key="p.title" class="flex gap-4">
            <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/15">
              <component :is="p.icon" class="h-5 w-5" />
            </span>
            <div>
              <p class="font-semibold">{{ p.title }}</p>
              <p class="text-sm text-primary-100">{{ p.text }}</p>
            </div>
          </li>
        </ul>
      </div>
      <p class="relative text-sm text-primary-200">© 2026 Marketplace</p>
    </div>

    <div class="flex items-center justify-center bg-slate-50 p-6">
      <div class="w-full max-w-md">
        <RouterView />
      </div>
    </div>
  </div>
</template>
