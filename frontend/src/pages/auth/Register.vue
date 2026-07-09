<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Mail, Lock, AlertCircle } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import PasswordStrength from '@/components/ui/PasswordStrength.vue';
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
const agree = ref(false);
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
  if (!agree.value) {
    error.value = t('auth.mustAgree');
    return;
  }
  if (!run()) return;
  loading.value = true;
  try {
    await auth.register(form.value);
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
  <div class="card p-7 sm:p-8">
    <h1 class="font-heading text-2xl font-bold">{{ $t('auth.createAccount') }}</h1>
    <p class="mt-1 text-sm text-muted">{{ $t('auth.registerSubtitle') }}</p>

    <div v-if="error" class="mt-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
      <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> <span>{{ error }}</span>
    </div>

    <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
      <FormField v-model="form.email" :icon="Mail" :label="$t('common.email')" type="email" placeholder="you@example.com" autocomplete="email" autofocus :error="errors.email" @update:model-value="clear('email')" />
      <div>
        <FormField v-model="form.password" :icon="Lock" :label="$t('auth.password')" type="password" placeholder="••••••••" autocomplete="new-password" :error="errors.password" @update:model-value="clear('password')" />
        <PasswordStrength :value="form.password" />
      </div>
      <FormField v-model="form.password_confirm" :icon="Lock" :label="$t('auth.confirmPassword')" type="password" placeholder="••••••••" autocomplete="new-password" :error="errors.password_confirm" @update:model-value="clear('password_confirm')" />

      <label class="flex cursor-pointer items-start gap-2 text-sm text-muted">
        <input v-model="agree" type="checkbox" class="mt-0.5 rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
        <span>{{ $t('auth.agreePrefix') }} <RouterLink :to="{ name: 'support' }" class="font-medium text-primary-600 hover:underline">{{ $t('auth.terms') }}</RouterLink></span>
      </label>

      <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
        <Spinner v-if="loading" :size="18" /><span v-else>{{ $t('auth.createAccount') }}</span>
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-muted">
      {{ $t('auth.alreadyHave') }}
      <RouterLink :to="{ name: 'login' }" class="font-semibold text-primary-600 hover:underline">{{ $t('auth.signIn') }}</RouterLink>
    </p>
  </div>
</template>
