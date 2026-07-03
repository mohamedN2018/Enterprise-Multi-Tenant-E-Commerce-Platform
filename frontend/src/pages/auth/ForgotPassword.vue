<script setup>
import { ref } from 'vue';
import { MailCheck } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { apiPost, errorMessage } from '@/services/http';

const email = ref('');
const loading = ref(false);
const sent = ref(false);
const error = ref('');

const submit = async () => {
  error.value = '';
  loading.value = true;
  try {
    await apiPost('/auth/password/reset/', { email: email.value });
    sent.value = true;
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="card p-8">
    <template v-if="sent">
      <span class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-emerald-100 text-emerald-600"><MailCheck class="h-7 w-7" /></span>
      <h1 class="text-center text-2xl font-bold">{{ $t('auth.checkEmail') }}</h1>
      <p class="mt-2 text-center text-sm text-muted">{{ $t('auth.resetSentMsg', { email }) }}</p>
      <RouterLink :to="{ name: 'login' }" class="btn btn-primary btn-lg mt-6 w-full">{{ $t('auth.backToSignIn') }}</RouterLink>
    </template>
    <template v-else>
      <h1 class="text-2xl font-bold">{{ $t('auth.forgotPassword') }}</h1>
      <p class="mt-1 text-sm text-muted">{{ $t('auth.forgotSubtitle') }}</p>
      <div v-if="error" class="mt-4 rounded-lg border border-secondary-200 bg-secondary-50 px-4 py-2.5 text-sm text-secondary-700">{{ error }}</div>
      <form class="mt-6 space-y-4" @submit.prevent="submit">
        <FormField v-model="email" :label="$t('common.email')" type="email" placeholder="you@example.com" autocomplete="email" required />
        <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading"><Spinner v-if="loading" :size="18" /><span v-else>{{ $t('auth.sendResetLink') }}</span></button>
      </form>
      <p class="mt-6 text-center text-sm text-muted"><RouterLink :to="{ name: 'login' }" class="font-semibold text-primary-600 hover:underline">{{ $t('auth.backToSignIn') }}</RouterLink></p>
    </template>
  </div>
</template>
