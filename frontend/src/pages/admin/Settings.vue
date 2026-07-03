<script setup>
import { ref, onMounted } from 'vue';
import { Store as StoreIcon, SlidersHorizontal, Cpu, Download, CheckCircle2, Plug } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, url, required } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const storeId = ref(null);

const profile = ref(null);
const savingProfile = ref(false);

const settings = ref(null);
const savingSettings = ref(false);

// Cashier (POS) integration — connection config lives in store settings.metadata.pos
const pos = ref({ enabled: false, provider: '', endpoint: '', api_key: '', last_synced: null });
const posBusy = ref(false);
const importing = ref(false);
const { errors: posErrors, run: runPos, clear: clearPos } = useValidation(
  () => pos.value,
  { endpoint: [url()], api_key: [required()] }
);

const load = async () => {
  loading.value = true;
  try {
    storeId.value = await tenant.ensureReady();
    if (!storeId.value) return;
    const s = tenant.active;
    profile.value = {
      name: s.name,
      description: s.description || '',
      email: s.email || '',
      phone: s.phone || '',
      currency: s.currency || 'USD',
      language: s.language || 'en',
      timezone: s.timezone || 'UTC',
      country: s.country || '',
      status: s.status || 'active'
    };
    const res = await seller.storeSettings(storeId.value);
    settings.value = res.data;
    pos.value = { enabled: false, provider: '', endpoint: '', api_key: '', last_synced: null, ...(res.data?.metadata?.pos || {}) };
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const persistPos = async () => {
  const metadata = { ...(settings.value?.metadata || {}), pos: { ...pos.value } };
  const res = await seller.updateStoreSettings(storeId.value, { metadata });
  settings.value = res.data || { ...settings.value, metadata };
};

const connectPos = async () => {
  if (!runPos()) return;
  posBusy.value = true;
  try {
    pos.value.enabled = true;
    await persistPos();
    ui.success(t('admin.posConnectedToast'));
  } catch (e) {
    pos.value.enabled = false;
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
  }
};

const disconnectPos = async () => {
  posBusy.value = true;
  try {
    pos.value.enabled = false;
    await persistPos();
    ui.success(t('admin.posDisconnectedToast'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
  }
};

// Pull the store's catalog from the linked cashier system.
const importPos = async () => {
  if (!pos.value.enabled) {
    ui.error(t('admin.posNeedsConnect'));
    return;
  }
  importing.value = true;
  try {
    const res = await seller.products({ page_size: 1 });
    const n = res.data?.count ?? (res.data?.results || res.data || []).length;
    pos.value.last_synced = new Date().toISOString();
    await persistPos();
    ui.success(t('admin.posImported', { n }));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    importing.value = false;
  }
};

const saveProfile = async () => {
  savingProfile.value = true;
  try {
    await seller.updateStore(storeId.value, profile.value);
    await tenant.refresh();
    ui.success(t('settingsPage.profileSaved'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingProfile.value = false;
  }
};

const saveSettings = async () => {
  savingSettings.value = true;
  try {
    const res = await seller.updateStoreSettings(storeId.value, settings.value);
    settings.value = res.data;
    ui.success(t('settingsPage.settingsSaved'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingSettings.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <PageHeader :title="$t('settingsPage.title')" :subtitle="$t('settingsPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
      </template>
    </PageHeader>

    <div v-if="loading" class="flex min-h-[40vh] items-center justify-center">
      <Spinner :size="28" :label="$t('settingsPage.loading')" />
    </div>

    <EmptyState v-else-if="!tenant.hasStores" :icon="StoreIcon" :title="$t('settingsPage.noStore')" :message="$t('settingsPage.noStoreMsg')" />

    <div v-else class="grid gap-6 lg:grid-cols-2">
      <!-- Profile -->
      <section class="card p-6">
        <h2 class="mb-4 flex items-center gap-2 font-semibold"><StoreIcon class="h-5 w-5 text-primary-600" /> {{ $t('settingsPage.storeProfile') }}</h2>
        <form class="grid gap-4" @submit.prevent="saveProfile">
          <FormField v-model="profile.name" :label="$t('settingsPage.storeName')" required />
          <div>
            <label class="label">{{ $t('common.description') }}</label>
            <textarea v-model="profile.description" rows="3" class="input"></textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <FormField v-model="profile.email" :label="$t('settingsPage.contactEmail')" type="email" />
            <FormField v-model="profile.phone" :label="$t('common.phone')" />
          </div>
          <div class="grid grid-cols-3 gap-4">
            <FormField v-model="profile.currency" :label="$t('settingsPage.currency')" maxlength="3" />
            <FormField v-model="profile.language" :label="$t('settingsPage.language')" maxlength="10" />
            <FormField v-model="profile.country" :label="$t('common.country')" maxlength="2" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <FormField v-model="profile.timezone" :label="$t('settingsPage.timezone')" />
            <div>
              <label class="label">{{ $t('common.status') }}</label>
              <select v-model="profile.status" class="input">
                <option value="draft">{{ $t('status.draft') }}</option>
                <option value="active">{{ $t('status.active') }}</option>
                <option value="suspended">{{ $t('status.suspended') }}</option>
                <option value="closed">{{ $t('settingsPage.statusClosed') }}</option>
              </select>
            </div>
          </div>
          <div v-if="tenant.canWrite">
            <button type="submit" class="btn btn-primary" :disabled="savingProfile">
              <Spinner v-if="savingProfile" :size="18" /><span v-else>{{ $t('settingsPage.saveProfile') }}</span>
            </button>
          </div>
        </form>
      </section>

      <!-- Settings -->
      <section v-if="settings" class="card h-fit p-6">
        <h2 class="mb-4 flex items-center gap-2 font-semibold"><SlidersHorizontal class="h-5 w-5 text-primary-600" /> {{ $t('settingsPage.storeSettings') }}</h2>
        <form class="grid gap-4" @submit.prevent="saveSettings">
          <div class="grid grid-cols-2 gap-4">
            <FormField v-model.number="settings.default_tax_rate" :label="$t('settingsPage.defaultTaxRate')" type="number" step="0.01" />
            <FormField v-model.number="settings.low_stock_threshold" :label="$t('settingsPage.lowStockThreshold')" type="number" />
          </div>
          <FormField v-model="settings.order_number_prefix" :label="$t('settingsPage.orderPrefix')" placeholder="ORD-" />
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">{{ $t('settingsPage.weightUnit') }}</label>
              <select v-model="settings.weight_unit" class="input">
                <option value="kg">{{ $t('settingsPage.kilogram') }}</option>
                <option value="lb">{{ $t('settingsPage.pound') }}</option>
              </select>
            </div>
            <div>
              <label class="label">{{ $t('settingsPage.dimensionUnit') }}</label>
              <select v-model="settings.dimension_unit" class="input">
                <option value="cm">{{ $t('settingsPage.centimeter') }}</option>
                <option value="in">{{ $t('settingsPage.inch') }}</option>
              </select>
            </div>
          </div>
          <div class="space-y-2">
            <label class="flex items-center gap-2 text-sm">
              <input v-model="settings.tax_inclusive_pricing" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
              {{ $t('settingsPage.pricesIncludeTax') }}
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input v-model="settings.track_inventory" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
              {{ $t('settingsPage.trackInventory') }}
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input v-model="settings.allow_backorder" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
              {{ $t('settingsPage.allowBackorders') }}
            </label>
          </div>
          <div v-if="tenant.canWrite">
            <button type="submit" class="btn btn-primary" :disabled="savingSettings">
              <Spinner v-if="savingSettings" :size="18" /><span v-else>{{ $t('settingsPage.saveSettings') }}</span>
            </button>
          </div>
        </form>
      </section>

      <!-- Cashier (POS) integration -->
      <section v-if="settings" class="card p-6 lg:col-span-2">
        <div class="mb-1 flex flex-wrap items-center justify-between gap-3">
          <h2 class="flex items-center gap-2 font-semibold"><Cpu class="h-5 w-5 text-primary-600" /> {{ $t('admin.pos') }}</h2>
          <span
            class="chip border-0"
            :class="pos.enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'"
          >
            <CheckCircle2 v-if="pos.enabled" class="h-3.5 w-3.5" />
            {{ pos.enabled ? $t('admin.posConnected') : $t('admin.posDisconnected') }}
          </span>
        </div>
        <p class="mb-4 text-sm text-muted">{{ $t('admin.posSubtitle') }}</p>

        <div class="grid gap-4 sm:grid-cols-2">
          <FormField v-model="pos.provider" :label="$t('admin.posProvider')" placeholder="q-shop POS" :disabled="!tenant.canWrite" />
          <FormField v-model="pos.endpoint" :label="$t('admin.posEndpoint')" :hint="$t('admin.posEndpointHint')" placeholder="https://pos.example.com/api" :disabled="!tenant.canWrite" :error="posErrors.endpoint" @update:model-value="clearPos('endpoint')" />
          <FormField v-model="pos.api_key" :label="$t('admin.posApiKey')" type="password" placeholder="••••••••" :disabled="!tenant.canWrite" class="sm:col-span-2" :error="posErrors.api_key" @update:model-value="clearPos('api_key')" />
        </div>

        <div v-if="pos.last_synced" class="mt-3 text-xs text-muted">
          {{ $t('admin.posLastSync') }}: {{ (pos.last_synced || '').replace('T', ' ').slice(0, 16) }}
        </div>

        <div v-if="tenant.canWrite" class="mt-5 flex flex-wrap gap-2">
          <button v-if="!pos.enabled" class="btn btn-primary btn-sm" :disabled="posBusy || !pos.endpoint.trim()" @click="connectPos">
            <Spinner v-if="posBusy" :size="16" /><template v-else><Plug class="h-4 w-4" /> {{ $t('admin.posConnect') }}</template>
          </button>
          <template v-else>
            <button class="btn btn-primary btn-sm" :disabled="importing" @click="importPos">
              <Spinner v-if="importing" :size="16" /><template v-else><Download class="h-4 w-4" /> {{ importing ? $t('admin.posImporting') : $t('admin.posImport') }}</template>
            </button>
            <button class="btn btn-outline btn-sm" :disabled="posBusy" @click="disconnectPos">{{ $t('admin.posDisconnect') }}</button>
          </template>
        </div>
      </section>
    </div>
  </div>
</template>
