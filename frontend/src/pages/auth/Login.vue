<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import { errorMessage } from '@/services/http';

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
    ui.success('Welcome back!');
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
    <h1 class="text-2xl font-bold">Sign in</h1>
    <p class="mt-1 text-sm text-slate-500">Welcome back. Please enter your details.</p>

    <div v-if="error" class="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
      {{ error }}
    </div>

    <form class="mt-6 space-y-4" @submit.prevent="submit">
      <FormField
        v-model="form.email"
        label="Email"
        type="email"
        placeholder="you@example.com"
        autocomplete="email"
        required
      />
      <FormField
        v-model="form.password"
        label="Password"
        type="password"
        placeholder="••••••••"
        autocomplete="current-password"
        required
      />
      <button type="submit" class="btn btn-primary btn-lg w-full" :disabled="loading">
        <Spinner v-if="loading" :size="18" />
        <span v-else>Sign in</span>
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-slate-500">
      Don't have an account?
      <RouterLink :to="{ name: 'register' }" class="font-semibold text-primary-600 hover:underline">
        Create one
      </RouterLink>
    </p>
  </div>
</template>
