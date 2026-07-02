<script setup>
import { ShieldCheck, Store, TrendingUp } from 'lucide-vue-next';

const perks = [
  { icon: Store, title: 'تسوّق من متاجر موثوقة', text: 'آلاف المنتجات في مكان واحد.' },
  { icon: TrendingUp, title: 'عروض وخصومات', text: 'أفضل الأسعار من بائعين مستقلين.' },
  { icon: ShieldCheck, title: 'دفع آمن', text: 'حماية كاملة لكل عملية شراء.' }
];
</script>

<template>
  <div class="grid min-h-screen lg:grid-cols-2">
    <div class="relative hidden overflow-hidden bg-primary-700 p-12 text-white lg:flex lg:flex-col">
      <div class="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary-500/40 blur-3xl"></div>
      <div class="absolute -bottom-24 -left-16 h-72 w-72 rounded-full bg-primary-400/30 blur-3xl"></div>
      <RouterLink :to="{ name: 'home' }" class="relative">
        <img src="/brand/dark-logo.png" alt="q-shop" class="h-16 w-auto" />
      </RouterLink>
      <div class="relative my-auto max-w-md">
        <h1 class="text-3xl font-bold leading-tight">تسوّق أذكى مع q-shop.</h1>
        <p class="mt-3 text-primary-100">
          كل ما تحتاجه للتسوّق من متاجر مستقلة موثوقة — منتجات متنوّعة، دفع آمن، وتوصيل سريع.
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
      <p class="relative text-sm text-primary-200">© 2026 q-shop</p>
    </div>

    <div class="flex items-center justify-center bg-slate-50 p-6">
      <div class="w-full max-w-md">
        <RouterView />
      </div>
    </div>
  </div>
</template>
