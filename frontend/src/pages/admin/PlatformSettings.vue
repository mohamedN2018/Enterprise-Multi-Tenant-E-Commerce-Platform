<script setup>
import { ref, onMounted } from 'vue';
import { Settings, Check, RotateCcw, Store as StoreIcon, Phone, Share2, Globe2 } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { brand } from '@/theme';
import { t } from '@/i18n';

const ui = useUiStore();

const DEFAULT = {
  platform_name: 'q-shop',
  support_email: 'support@q-shop.com',
  support_phone: '+0121234567890',
  address: '123 Market Street, Cairo',
  facebook: '',
  twitter: '',
  instagram: '',
  linkedin: '',
  default_language: 'ar',
  default_mode: 'light'
};

const form = ref({ ...DEFAULT });
const loading = ref(true);
const saving = ref(false);

const save = async () => {
  saving.value = true;
  try {
    const res = await seller.updatePlatformTheme(form.value);
    // Push the fresh config into the live brand so the footer/contacts update now.
    brand.value = res.data;
    localStorage.setItem('brand', JSON.stringify(res.data));
    ui.success(t('platformSettings.saved'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    saving.value = false;
  }
};

const resetDefault = () => {
  form.value = { ...DEFAULT };
};

onMounted(async () => {
  try {
    const res = await seller.getPlatformTheme();
    form.value = { ...DEFAULT, ...res.data };
  } catch {
    form.value = { ...DEFAULT, ...(brand.value || {}) };
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div>
    <PageHeader :title="$t('platformSettings.title')" :subtitle="$t('platformSettings.subtitle')" />

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="28" /></div>

    <div v-else class="max-w-3xl space-y-6">
      <!-- Identity -->
      <section class="card p-6">
        <h2 class="mb-4 flex items-center gap-2 font-semibold"><StoreIcon class="h-5 w-5 text-primary-600" /> {{ $t('platformSettings.identity') }}</h2>
        <FormField v-model="form.platform_name" :label="$t('platformSettings.platformName')" :hint="$t('platformSettings.platformNameHint')" placeholder="q-shop" maxlength="60" />
      </section>

      <!-- Contact (shown in the storefront footer + top bar) -->
      <section class="card p-6">
        <h2 class="mb-1 flex items-center gap-2 font-semibold"><Phone class="h-5 w-5 text-primary-600" /> {{ $t('platformSettings.contact') }}</h2>
        <p class="mb-4 text-sm text-muted">{{ $t('platformSettings.contactHint') }}</p>
        <div class="grid gap-5 sm:grid-cols-2">
          <FormField v-model="form.support_email" :label="$t('platformSettings.supportEmail')" type="email" placeholder="support@q-shop.com" />
          <FormField v-model="form.support_phone" :label="$t('platformSettings.supportPhone')" placeholder="+0121234567890" />
          <FormField v-model="form.address" :label="$t('platformSettings.address')" class="sm:col-span-2" placeholder="123 Market Street, Cairo" maxlength="200" />
        </div>
      </section>

      <!-- Social links -->
      <section class="card p-6">
        <h2 class="mb-1 flex items-center gap-2 font-semibold"><Share2 class="h-5 w-5 text-primary-600" /> {{ $t('platformSettings.social') }}</h2>
        <p class="mb-4 text-sm text-muted">{{ $t('platformSettings.socialHint') }}</p>
        <div class="grid gap-5 sm:grid-cols-2">
          <FormField v-model="form.facebook" label="Facebook" placeholder="https://facebook.com/…" />
          <FormField v-model="form.twitter" label="Twitter / X" placeholder="https://x.com/…" />
          <FormField v-model="form.instagram" label="Instagram" placeholder="https://instagram.com/…" />
          <FormField v-model="form.linkedin" label="LinkedIn" placeholder="https://linkedin.com/…" />
        </div>
      </section>

      <!-- Defaults for new visitors -->
      <section class="card p-6">
        <h2 class="mb-1 flex items-center gap-2 font-semibold"><Globe2 class="h-5 w-5 text-primary-600" /> {{ $t('platformSettings.defaults') }}</h2>
        <p class="mb-4 text-sm text-muted">{{ $t('platformSettings.defaultsHint') }}</p>
        <div class="grid gap-5 sm:grid-cols-2">
          <label class="block">
            <span class="label">{{ $t('platformSettings.defaultLanguage') }}</span>
            <select v-model="form.default_language" class="input">
              <option value="ar">{{ $t('platformSettings.arabic') }}</option>
              <option value="en">{{ $t('platformSettings.english') }}</option>
            </select>
          </label>
          <label class="block">
            <span class="label">{{ $t('platformSettings.defaultMode') }}</span>
            <select v-model="form.default_mode" class="input">
              <option value="light">{{ $t('platformSettings.light') }}</option>
              <option value="dark">{{ $t('platformSettings.dark') }}</option>
            </select>
          </label>
        </div>
      </section>

      <div class="flex flex-wrap gap-2">
        <button class="btn btn-primary" :disabled="saving" @click="save">
          <Spinner v-if="saving" :size="18" /><template v-else><Check class="h-4 w-4" /> {{ $t('platformSettings.save') }}</template>
        </button>
        <button class="btn btn-outline" @click="resetDefault"><RotateCcw class="h-4 w-4" /> {{ $t('appearance.reset') }}</button>
      </div>
      <p class="text-xs text-muted">{{ $t('platformSettings.appliesHint') }}</p>
    </div>
  </div>
</template>
