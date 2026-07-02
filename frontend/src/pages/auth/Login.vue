<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();

const form = ref({ email: '', password: '' });
const loading = ref(false);
const error = ref('');

const submit = async () => {
  error.value = '';
  loading.value = true;
  try {
    await auth.login(form.value.email, form.value.password);
    ui.success(t('auth.welcomeBack'));
    const redirect = route.query.redirect;
    router.push(typeof redirect === 'string' ? redirect : { name: 'home' });
  } catch (e) {
    error.value = errorMessage(e);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="card p-8">
    <h1 class="text-2xl font-bold">{{ $t('auth.signIn') }}</h1>
    <p class="mt-1 text-sm text-slate-500">{{ $t('auth.signInSubtitle') }}</p>

    <div v-if="error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
      {{ error }}
    </div>

    <form class="mt-6 space-y-4" @submit.prevent="submit">
      <FormField
        v-model="form.email"
        :label="$t('common.email')"
        type="email"
        placeholder="you@example.com"
        autocomplete="email"
        required
      />
      <FormField
        v-model="form.password"
        :label="$t('auth.password')"
        type="password"
        placeholder="••••••••"
        autocomplete="current-password"
        required
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
  </div>
</template>
