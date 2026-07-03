<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, email, min, sameAs } from '@/utils/validators';

const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();

const form = ref({ email: '', password: '', password_confirm: '' });
const loading = ref(false);
const error = ref('');

const { errors, run, clear } = useValidation(
  () => form.value,
  () => ({
    email: [email()],
    password: [min(8)],
    password_confirm: [sameAs(() => form.value.password, t('auth.passwordsNoMatch'))]
  })
);

const submit = async () => {
  error.value = '';
  if (!run()) return;
  loading.value = true;
  try {
    await auth.register(form.value);
    // Registration requires email verification before login, so send the user
    // to sign in with a confirmation message rather than auto-authenticating.
    ui.success(t('auth.accountCreated'));
    router.push({ name: 'login' });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="card p-8">
    <h1 class="text-2xl font-bold">{{ $t('auth.createAccount') }}</h1>
    <p class="mt-1 text-sm text-slate-500">{{ $t('auth.registerSubtitle') }}</p>

    <div v-if="error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
      {{ error }}
    </div>

    <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
      <FormField v-model="form.email" :label="$t('common.email')" type="email" placeholder="you@example.com" autocomplete="email" :error="errors.email" @update:model-value="clear('email')" />
      <FormField v-model="form.password" :label="$t('auth.password')" type="password" placeholder="8+" autocomplete="new-password" :error="errors.password" @update:model-value="clear('password')" />
      <FormField v-model="form.password_confirm" :label="$t('auth.confirmPassword')" type="password" autocomplete="new-password" :error="errors.password_confirm" @update:model-value="clear('password_confirm')" />
      <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
        <Spinner v-if="loading" :size="18" /><span v-else>{{ $t('auth.createAccount') }}</span>
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-500">
      {{ $t('auth.alreadyHave') }}
      <RouterLink :to="{ name: 'login' }" class="font-semibold text-primary-600 hover:underline">{{ $t('auth.signIn') }}</RouterLink>
    </p>
  </div>
</template>
