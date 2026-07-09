<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Mail, Lock, AlertCircle, ShieldCheck } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { apiPost, errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, email as emailRule, required } from '@/utils/validators';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();

const form = ref({ email: '', password: '' });
const remember = ref(false);
const loading = ref(false);
const error = ref('');
const needsVerify = ref(false); // show a "resend verification" action
const resending = ref(false);

const { errors, run, clear } = useValidation(() => form.value, {
  email: [emailRule()],
  password: [required()]
});

// One form for everyone — recognise WHO signed in and route them:
//   super-admin → control centre · seller/staff → console · customer → shop.
const landingRoute = () => {
  if (auth.user?.is_superuser) return { name: 'admin-platform' };
  return auth.isSeller ? { name: 'seller-dashboard' } : { name: 'home' };
};

const submit = async () => {
  error.value = '';
  needsVerify.value = false;
  if (!run()) return;
  loading.value = true;
  try {
    await auth.login(form.value.email.trim(), form.value.password, remember.value);
    ui.success(t('auth.welcomeBack'));
    const redirect = route.query.redirect;
    router.push(typeof redirect === 'string' ? redirect : landingRoute());
  } catch (e) {
    const code = e?.response?.data?.error_code;
    const status = e?.response?.status;
    if (code === 'email_not_verified') {
      needsVerify.value = true;
      error.value = t('auth.emailNotVerified');
    } else if (status === 429) {
      error.value = t('auth.tooManyAttempts');
    } else {
      error.value = errorMessage(e);
    }
  } finally {
    loading.value = false;
  }
};

const resendVerification = async () => {
  resending.value = true;
  try {
    await apiPost('/auth/resend-verification/', { email: form.value.email.trim() });
    ui.success(t('auth.resendSuccess'));
    needsVerify.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    resending.value = false;
  }
};
</script>

<template>
  <div class="card p-7 sm:p-8">
    <h1 class="font-heading text-2xl font-bold">{{ $t('auth.signIn') }}</h1>
    <p class="mt-1 text-sm text-muted">{{ $t('auth.unifiedSubtitle') }}</p>

    <div v-if="error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      <div class="flex items-start gap-2"><AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> <span>{{ error }}</span></div>
      <button v-if="needsVerify" type="button" class="btn btn-outline btn-sm mt-3" :disabled="resending" @click="resendVerification">
        <Spinner v-if="resending" :size="14" /><template v-else><Mail class="h-3.5 w-3.5" /> {{ $t('auth.resendEmailBtn') }}</template>
      </button>
    </div>

    <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
      <FormField v-model="form.email" :icon="Mail" :label="$t('common.email')" type="email" placeholder="you@example.com" autocomplete="email" autofocus :error="errors.email" @update:model-value="clear('email')" />
      <FormField v-model="form.password" :icon="Lock" :label="$t('auth.password')" type="password" placeholder="••••••••" autocomplete="current-password" :error="errors.password" @update:model-value="clear('password')" />

      <div class="flex flex-wrap items-center justify-between gap-2">
        <label class="flex cursor-pointer items-center gap-2 text-sm text-muted">
          <input v-model="remember" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('auth.rememberMe') }}
        </label>
        <RouterLink :to="{ name: 'forgot-password' }" class="text-sm font-medium text-primary-600 hover:underline">{{ $t('auth.forgotPassword') }}</RouterLink>
      </div>

      <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
        <Spinner v-if="loading" :size="18" /><span v-else>{{ $t('auth.signIn') }}</span>
      </button>
    </form>

    <!-- Everyone uses this one form; the system routes each role automatically. -->
    <p class="mt-4 flex items-center justify-center gap-1.5 text-center text-xs text-muted">
      <ShieldCheck class="h-3.5 w-3.5 text-primary-500" /> {{ $t('auth.autoRouteHint') }}
    </p>

    <p class="mt-5 border-t border-slate-100 pt-5 text-center text-sm text-muted dark:border-slate-800">
      {{ $t('auth.noAccount') }}
      <RouterLink :to="{ name: 'register' }" class="font-semibold text-primary-600 hover:underline">{{ $t('auth.createOne') }}</RouterLink>
    </p>
  </div>
</template>
