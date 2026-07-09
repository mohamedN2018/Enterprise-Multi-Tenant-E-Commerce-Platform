<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Mail, Lock, Store as StoreIcon, ShoppingBag, AlertCircle } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, email as emailRule, required } from '@/utils/validators';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();

// Seller mode = the dedicated /auth/seller entry.
const sellerMode = computed(() => route.meta.seller === true);

const form = ref({ email: '', password: '' });
const remember = ref(false);
const loading = ref(false);
const error = ref('');

const { errors, run, clear } = useValidation(() => form.value, {
  email: [emailRule()],
  password: [required()]
});

// Recognise WHO signed in and land them in the right place.
const landingRoute = () => {
  if (auth.user?.is_superuser) return { name: 'admin-platform' };
  return auth.isSeller ? { name: 'seller-dashboard' } : { name: 'home' };
};

const submit = async () => {
  error.value = '';
  if (!run()) return;
  loading.value = true;
  try {
    await auth.login(form.value.email, form.value.password, remember.value);
    ui.success(t('auth.welcomeBack'));
    const redirect = route.query.redirect;
    if (typeof redirect === 'string') router.push(redirect);
    else router.push(landingRoute());
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="card p-7 sm:p-8">
    <!-- Customer / seller segmented toggle -->
    <div class="mb-6 grid grid-cols-2 gap-1 rounded-xl bg-lightbg p-1">
      <RouterLink
        :to="{ name: 'login' }"
        class="flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-semibold transition"
        :class="!sellerMode ? 'bg-white text-primary-700 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-muted hover:text-ink'"
      >
        <ShoppingBag class="h-4 w-4" /> {{ $t('auth.asCustomer') }}
      </RouterLink>
      <RouterLink
        :to="{ name: 'seller-login' }"
        class="flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-semibold transition"
        :class="sellerMode ? 'bg-white text-primary-700 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-muted hover:text-ink'"
      >
        <StoreIcon class="h-4 w-4" /> {{ $t('auth.asSeller') }}
      </RouterLink>
    </div>

    <h1 class="font-heading text-2xl font-bold">{{ sellerMode ? $t('auth.sellerSignIn') : $t('auth.signIn') }}</h1>
    <p class="mt-1 text-sm text-muted">{{ sellerMode ? $t('auth.sellerSubtitle') : $t('auth.signInSubtitle') }}</p>

    <div v-if="error" class="mt-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
      <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" /> <span>{{ error }}</span>
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
        <Spinner v-if="loading" :size="18" />
        <span v-else>{{ sellerMode ? $t('auth.sellerSignIn') : $t('auth.signIn') }}</span>
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-muted">
      {{ $t('auth.noAccount') }}
      <RouterLink :to="{ name: 'register' }" class="font-semibold text-primary-600 hover:underline">{{ $t('auth.createOne') }}</RouterLink>
    </p>
  </div>
</template>
