<script setup>
import { Compass } from 'lucide-vue-next';
</script>

<template>
  <div class="container flex min-h-[60vh] flex-col items-center justify-center py-16 text-center">
    <span class="grid h-16 w-16 place-items-center rounded-2xl bg-primary-100 text-primary-600">
      <Compass class="h-8 w-8" />
    </span>
    <p class="mt-6 text-5xl font-bold text-ink">404</p>
    <h1 class="mt-2 text-xl font-semibold">{{ $t('common.pageNotFound') }}</h1>
    <p class="mt-2 max-w-sm text-slate-500">
      {{ $t('common.pageNotFoundMsg') }}
    </p>
    <div class="mt-6 flex gap-3">
      <RouterLink :to="{ name: 'home' }" class="btn btn-primary">{{ $t('common.backHome') }}</RouterLink>
      <RouterLink :to="{ name: 'products' }" class="btn btn-outline">{{ $t('common.browseProducts') }}</RouterLink>
    </div>
  </div>
</template>
