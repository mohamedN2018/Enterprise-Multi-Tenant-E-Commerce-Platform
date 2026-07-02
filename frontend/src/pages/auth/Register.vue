<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { errorMessage } from '@/services/http';

const router = useRouter();
const auth = useAuthStore();
const ui = useUiStore();

const form = ref({ email: '', password: '', password_confirm: '' });
const loading = ref(false);
const error = ref('');

const submit = async () => {
  error.value = '';
  if (form.value.password !== form.value.password_confirm) {
    error.value = 'Passwords do not match.';
    return;
  }
  loading.value = true;
  try {
    await auth.register(form.value);
    // Registration requires email verification before login, so send the user
    // to sign in with a confirmation message rather than auto-authenticating.
    ui.success('Account created! Please sign in.');
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
    <h1 class="text-2xl font-bold">Create your account</h1>
    <p class="mt-1 text-sm text-slate-500">Start shopping or open your own store in minutes.</p>

    <div v-if="error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
      {{ error }}
    </div>

    <form class="mt-6 space-y-4" @submit.prevent="submit">
      <FormField v-model="form.email" label="Email" type="email" placeholder="you@example.com" autocomplete="email" required />
      <FormField v-model="form.password" label="Password" type="password" placeholder="At least 8 characters" autocomplete="new-password" required />
      <FormField v-model="form.password_confirm" label="Confirm password" type="password" placeholder="Repeat your password" autocomplete="new-password" required />
      <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
        <Spinner v-if="loading" :size="18" /><span v-else>Create account</span>
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-500">
      Already have an account?
      <RouterLink :to="{ name: 'login' }" class="font-semibold text-primary-600 hover:underline">Sign in</RouterLink>
    </p>
  </div>
</template>
