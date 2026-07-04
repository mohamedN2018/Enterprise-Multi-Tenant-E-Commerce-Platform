<script setup>
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Store as StoreIcon } from 'lucide-vue-next';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, email, required } from '@/utils/validators';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();

// Seller mode = the dedicated /auth/seller entry: sends the user to the
// dashboard on success instead of the storefront home.
const sellerMode = computed(() => route.meta.seller === true);

const form = ref({ email: '', password: '' });
const loading = ref(false);
const error = ref('');

const { errors, run, clear } = useValidation(
  () => form.value,
  { email: [email()], password: [required()] }
);

const submit = async () => {
  error.value = '';
  if (!run()) return;
  loading.value = true;
  try {
    await auth.login(form.value.email, form.value.password);
    ui.success(t('auth.welcomeBack'));
    const redirect = route.query.redirect;
    if (typeof redirect === 'string') router.push(redirect);
    else if (auth.user?.is_superuser) router.push({ name: 'admin-platform' });
    else router.push({ name: sellerMode.value ? 'seller-dashboard' : 'home' });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="card p-8">
    <div v-if="sellerMode" class="mb-4 inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
      <StoreIcon class="h-3.5 w-3.5" /> {{ $t('admin.seller') }}
    </div>
    <h1 class="text-2xl font-bold">{{ sellerMode ? $t('auth.sellerSignIn') : $t('auth.signIn') }}</h1>
    <p class="mt-1 text-sm text-slate-500">{{ sellerMode ? $t('auth.sellerSubtitle') : $t('auth.signInSubtitle') }}</p>

    <div v-if="error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
      {{ error }}
    </div>

    <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
      <FormField
        v-model="form.email"
        :label="$t('common.email')"
        type="email"
        placeholder="you@example.com"
        autocomplete="email"
        :error="errors.email"
        @update:model-value="clear('email')"
      />
      <FormField
        v-model="form.password"
        :label="$t('auth.password')"
        type="password"
        placeholder="••••••••"
        autocomplete="current-password"
        :error="errors.password"
        @update:model-value="clear('password')"
      />
      <div class="text-end">
        <RouterLink :to="{ name: 'forgot-password' }" class="text-sm font-medium text-primary-600 hover:underline">{{ $t('auth.forgotPassword') }}</RouterLink>
      </div>
      <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
        <Spinner v-if="loading" :size="18" />
        <span v-else>{{ $t('auth.signIn') }}</span>
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-500">
      {{ $t('auth.noAccount') }}
      <RouterLink :to="{ name: 'register' }" class="font-semibold text-primary-600 hover:underline">
        {{ $t('auth.createOne') }}
      </RouterLink>
    </p>

    <div class="mt-4 border-t border-slate-100 pt-4 text-center">
      <RouterLink
        :to="{ name: sellerMode ? 'login' : 'seller-login' }"
        class="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:underline"
      >
        <StoreIcon class="h-4 w-4" /> {{ sellerMode ? $t('auth.customerLoginLink') : $t('auth.sellerLoginLink') }}
      </RouterLink>
    </div>
  </div>
</template>
