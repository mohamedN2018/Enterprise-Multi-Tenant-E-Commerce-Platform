<script setup>
import { computed } from 'vue';
import { ShieldCheck, Store, TrendingUp, ArrowLeft, Sun, Moon, Languages } from 'lucide-vue-next';
import { t, useI18n } from '@/i18n';
import { useTheme, brand } from '@/theme';

const { locale, setLocale } = useI18n();
const { theme, toggleTheme } = useTheme();

const platformName = computed(() => brand.value?.platform_name || 'q-shop');
const logo = computed(() => (theme.value === 'dark' ? '/brand/dark-logo.png' : '/brand/dark-logo.png'));

const perks = [
  { icon: Store, key: 'trusted' },
  { icon: TrendingUp, key: 'deals' },
  { icon: ShieldCheck, key: 'secure' }
];

const toggleLang = () => setLocale(locale.value === 'ar' ? 'en' : 'ar');
</script>

<template>
  <div class="grid min-h-screen lg:grid-cols-2">
    <!-- Brand panel (desktop) — themes with the platform's primary colour -->
    <div class="relative hidden overflow-hidden bg-gradient-to-br from-primary-700 via-primary-800 to-primary-900 p-12 text-white lg:flex lg:flex-col">
      <div class="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/15 blur-3xl"></div>
      <div class="pointer-events-none absolute -bottom-24 -left-16 h-72 w-72 rounded-full bg-secondary-500/25 blur-3xl"></div>

      <RouterLink :to="{ name: 'home' }" class="relative flex items-center gap-3">
        <img :src="logo" :alt="platformName" class="h-14 w-auto" />
      </RouterLink>

      <div class="relative my-auto max-w-md">
        <h1 class="font-heading text-3xl font-black leading-tight lg:text-4xl">{{ t('authPanel.title') }}</h1>
        <p class="mt-3 text-white/80">{{ t('authPanel.subtitle') }}</p>
        <ul class="mt-9 space-y-5">
          <li v-for="p in perks" :key="p.key" class="flex gap-4">
            <span class="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/15 ring-1 ring-white/20">
              <component :is="p.icon" class="h-5 w-5" />
            </span>
            <div>
              <p class="font-semibold">{{ t('authPanel.' + p.key + 'Title') }}</p>
              <p class="text-sm text-white/70">{{ t('authPanel.' + p.key + 'Text') }}</p>
            </div>
          </li>
        </ul>
      </div>

      <p class="relative text-sm text-white/60">© 2026 {{ platformName }}</p>
    </div>

    <!-- Form side -->
    <div class="relative flex flex-col bg-lightbg">
      <!-- Top bar: back to store + language & theme toggles (available pre-login) -->
      <div class="flex items-center justify-between p-4 sm:p-6">
        <RouterLink :to="{ name: 'home' }" class="inline-flex items-center gap-1.5 text-sm font-medium text-muted transition hover:text-primary-600">
          <ArrowLeft class="h-4 w-4 rtl:rotate-180" /> {{ t('authPanel.backToStore') }}
        </RouterLink>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-ink transition hover:border-primary-400 dark:border-slate-700"
            @click="toggleLang"
          >
            <Languages class="h-3.5 w-3.5" /> {{ locale === 'ar' ? 'EN' : 'ع' }}
          </button>
          <button
            type="button"
            class="grid h-8 w-8 place-items-center rounded-full border border-slate-200 bg-white text-ink transition hover:border-primary-400 dark:border-slate-700"
            :aria-label="theme === 'dark' ? 'Light mode' : 'Dark mode'"
            @click="toggleTheme"
          >
            <component :is="theme === 'dark' ? Sun : Moon" class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- Centered form -->
      <div class="flex flex-1 items-center justify-center px-5 pb-10 sm:px-6">
        <div class="auth-enter w-full max-w-md">
          <!-- Mobile logo (brand panel is desktop-only) -->
          <RouterLink :to="{ name: 'home' }" class="mb-6 flex justify-center lg:hidden">
            <img src="/brand/qtech-logo.png" :alt="platformName" class="h-11 w-auto dark:hidden" />
            <img src="/brand/dark-logo.png" :alt="platformName" class="hidden h-11 w-auto dark:block" />
          </RouterLink>
          <RouterView />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-enter {
  animation: authIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes authIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .auth-enter {
    animation: none;
  }
}
</style>
