<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { apiPost, errorMessage } from '@/services/http';
import { useUiStore } from '@/stores/ui';
import { t } from '@/i18n';
import { useValidation, required, min, sameAs } from '@/utils/validators';

const route = useRoute();
const router = useRouter();
const ui = useUiStore();

const form = ref({
  token: route.query.token || '',
  new_password: '',
  new_password_confirm: ''
});
const loading = ref(false);
const error = ref('');

const { errors, run, clear } = useValidation(
  () => form.value,
  () => ({
    token: route.query.token ? [] : [required()],
    new_password: [min(8)],
    new_password_confirm: [sameAs(() => form.value.new_password, t('auth.passwordsNoMatch'))]
  })
);

const submit = async () => {
  error.value = '';
  if (!run()) return;
  loading.value = true;
  try {
    await apiPost('/auth/password/reset/confirm/', form.value);
    ui.success(t('auth.resetDone'));
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
    <h1 class="text-2xl font-bold">{{ $t('auth.resetTitle') }}</h1>
    <p class="mt-1 text-sm text-muted">{{ $t('auth.resetSubtitle') }}</p>
    <div v-if="error" class="mt-4 rounded-lg border border-secondary-200 bg-secondary-50 px-4 py-2.5 text-sm text-secondary-700">{{ error }}</div>
    <form class="mt-6 space-y-4" novalidate @submit.prevent="submit">
      <FormField v-if="!route.query.token" v-model="form.token" :label="$t('auth.resetToken')" :placeholder="$t('auth.resetTokenPlaceholder')" :error="errors.token" @update:model-value="clear('token')" />
      <FormField v-model="form.new_password" :label="$t('auth.newPassword')" type="password" autocomplete="new-password" :error="errors.new_password" @update:model-value="clear('new_password')" />
      <FormField v-model="form.new_password_confirm" :label="$t('auth.confirmNewPassword')" type="password" autocomplete="new-password" :error="errors.new_password_confirm" @update:model-value="clear('new_password_confirm')" />
      <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading"><Spinner v-if="loading" :size="18" /><span v-else>{{ $t('auth.resetBtn') }}</span></button>
    </form>
    <p class="mt-6 text-center text-sm text-muted"><RouterLink :to="{ name: 'login' }" class="font-semibold text-primary-600 hover:underline">{{ $t('auth.backToSignIn') }}</RouterLink></p>
  </div>
</template>
