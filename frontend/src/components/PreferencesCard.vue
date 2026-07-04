<script setup>
import { Languages, Sun, Moon, Settings2 } from 'lucide-vue-next';
import { useI18n } from '@/i18n';
import { useTheme } from '@/theme';

const { t, locale, setLocale } = useI18n();
const { theme, setTheme } = useTheme();
</script>

<template>
  <section class="card p-6">
    <h2 class="mb-1 flex items-center gap-2 font-heading text-lg font-bold text-ink">
      <Settings2 class="h-5 w-5 text-primary-600" /> {{ t('prefs.title') }}
    </h2>
    <p class="mb-5 text-sm text-muted">{{ t('prefs.subtitle') }}</p>
    <div class="grid gap-5 sm:grid-cols-2">
      <div>
        <p class="label mb-2">{{ t('prefs.language') }}</p>
        <div class="flex gap-2">
          <button class="btn btn-sm flex-1" :class="locale === 'ar' ? 'btn-primary' : 'btn-outline'" @click="setLocale('ar')"><Languages class="h-4 w-4" /> {{ t('account.arabic') }}</button>
          <button class="btn btn-sm flex-1" :class="locale === 'en' ? 'btn-primary' : 'btn-outline'" @click="setLocale('en')"><Languages class="h-4 w-4" /> {{ t('account.english') }}</button>
        </div>
      </div>
      <div>
        <p class="label mb-2">{{ t('account.theme') }}</p>
        <div class="flex gap-2">
          <button class="btn btn-sm flex-1" :class="theme === 'light' ? 'btn-primary' : 'btn-outline'" @click="setTheme('light')"><Sun class="h-4 w-4" /> {{ t('account.light') }}</button>
          <button class="btn btn-sm flex-1" :class="theme === 'dark' ? 'btn-primary' : 'btn-outline'" @click="setTheme('dark')"><Moon class="h-4 w-4" /> {{ t('account.dark') }}</button>
        </div>
      </div>
    </div>
  </section>
</template>
