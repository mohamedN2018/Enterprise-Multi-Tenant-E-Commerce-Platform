<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { CheckCircle2, XCircle, Mail } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { apiPost, errorMessage } from '@/services/http';
import { useUiStore } from '@/stores/ui';

const route = useRoute();
const ui = useUiStore();

const state = ref('idle'); // idle | verifying | success | error
const message = ref('');
const token = ref(route.query.token || '');
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
    ui.success('If your account needs verification, a new email is on its way.');
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
      <Spinner :size="30" label="Verifying your email…" />
    </template>

    <template v-else-if="state === 'success'">
      <span class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-emerald-100 text-emerald-600"><CheckCircle2 class="h-7 w-7" /></span>
      <h1 class="text-2xl font-bold">Email verified!</h1>
      <p class="mt-2 text-sm text-muted">Your account is now verified. You can sign in.</p>
      <RouterLink :to="{ name: 'login' }" class="btn btn-primary btn-lg mt-6 w-full">Sign in</RouterLink>
    </template>

    <template v-else-if="state === 'error'">
      <span class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-secondary-100 text-secondary-600"><XCircle class="h-7 w-7" /></span>
      <h1 class="text-2xl font-bold">Verification failed</h1>
      <p class="mt-2 text-sm text-muted">{{ message || 'The link may be invalid or expired.' }}</p>
      <form class="mt-6 space-y-3 text-left" @submit.prevent="resend">
        <FormField v-model="resendEmail" label="Resend verification to" type="email" placeholder="you@example.com" required />
        <button type="submit" class="btn btn-outline w-full" :disabled="resending"><Mail class="h-4 w-4" /> Resend email</button>
      </form>
    </template>

    <template v-else>
      <span class="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-primary-100 text-primary-600"><Mail class="h-7 w-7" /></span>
      <h1 class="text-2xl font-bold">Verify your email</h1>
      <p class="mt-2 text-sm text-muted">Enter the token from your verification email.</p>
      <form class="mt-6 space-y-3 text-left" @submit.prevent="verify(token)">
        <FormField v-model="token" label="Verification token" required />
        <button type="submit" class="btn btn-primary w-full">Verify</button>
      </form>
    </template>
  </div>
</template>
