<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { CheckCircle2, XCircle, Mail } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { apiPost, errorMessage } from '@/services/http';
import { useUiStore } from '@/stores/ui';
import { t } from '@/i18n';
import { tokenFromUrl } from '@/utils/urlToken';

const route = useRoute();
const ui = useUiStore();

const state = ref('idle'); // idle | verifying | success | error
const message = ref('');
const token = ref(tokenFromUrl(route));
const resendEmail = ref('');
const resending = ref(false);

const verify = async (t) => {
  state.value = 'verifying';
  try {
    await apiPost('/auth/verify-email/', { token: t });
    state.value = 'success';
  } catch (e) {
    state.value = 'error';
    message.value = errorMessage(e);
  }
};

const resend = async () => {
  resending.value = true;
  try {
    await apiPost('/auth/resend-verification/', { email: resendEmail.value });
    ui.success(t('auth.resendSuccess'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    resending.value = false;
  }
};

onMounted(() => {
  if (token.value) verify(token.value);
});
</script>

<template>
  <div class="card p-8 text-center">
    <template v-if="state === 'verifying'">
      <Spinner :size="30" :label="$t('auth.verifying')" />
    </template>

    <template v-else-if="state === 'success'">
      <span class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-emerald-100 text-emerald-600"><CheckCircle2 class="h-7 w-7" /></span>
      <h1 class="text-2xl font-bold">{{ $t('auth.emailVerified') }}</h1>
      <p class="mt-2 text-sm text-muted">{{ $t('auth.verifiedMsg') }}</p>
      <RouterLink :to="{ name: 'login' }" class="btn btn-primary btn-lg mt-6 w-full">{{ $t('auth.signIn') }}</RouterLink>
    </template>

    <template v-else-if="state === 'error'">
      <span class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-secondary-100 text-secondary-600"><XCircle class="h-7 w-7" /></span>
      <h1 class="text-2xl font-bold">{{ $t('auth.verifyFailed') }}</h1>
      <p class="mt-2 text-sm text-muted">{{ message || $t('auth.linkInvalid') }}</p>
      <form class="mt-6 space-y-3 text-start" @submit.prevent="resend">
        <FormField v-model="resendEmail" :label="$t('auth.resendTo')" type="email" placeholder="you@example.com" required />
        <button type="submit" class="btn btn-outline w-full" :disabled="resending"><Mail class="h-4 w-4" /> {{ $t('auth.resendEmailBtn') }}</button>
      </form>
    </template>

    <template v-else>
      <span class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-primary-100 text-primary-600"><Mail class="h-7 w-7" /></span>
      <h1 class="text-2xl font-bold">{{ $t('auth.verifyTitle') }}</h1>
      <p class="mt-2 text-sm text-muted">{{ $t('auth.verifyPrompt') }}</p>
      <form class="mt-6 space-y-3 text-start" @submit.prevent="verify(token)">
        <FormField v-model="token" :label="$t('auth.verifyToken')" required />
        <button type="submit" class="btn btn-primary w-full">{{ $t('auth.verifyBtn') }}</button>
      </form>
    </template>
  </div>
</template>
