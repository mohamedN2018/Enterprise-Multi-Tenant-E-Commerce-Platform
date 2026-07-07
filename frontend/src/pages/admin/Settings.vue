<script setup>
import { ref, computed, onMounted } from 'vue';
import { Store as StoreIcon, SlidersHorizontal, Cpu, CheckCircle2, Plug, Download, Unlink } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import PreferencesCard from '@/components/PreferencesCard.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { pos } from '@/services/pos';
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

// Cashier (POS) integration — link an external q-shop POS and import its catalog.
// The store's backend pulls products over the provider API (server-to-server).
const posConn = ref(null); // the connected supplier (or null when not connected)
const posForm = ref({ provider: 'q-shop POS', api_url: '', api_key: '' });
const posBusy = ref(false);
const importing = ref(false);
const importSummary = ref(null); // { created, updated, skipped } after an import
const { errors: posErrors, run: runPos, clear: clearPos } = useValidation(
  () => posForm.value,
  { api_url: [required(), url()], api_key: [required()] }
);
// Linking a cashier is a store-settings action.
const canPos = computed(() => tenant.canArea('settings'));

const load = async () => {
  loading.value = true;
  try {
    storeId.value = await tenant.ensureReady();
    if (!storeId.value) return;
    const s = tenant.active;
    profile.value = {
      name: s.name,
      name_en: s.name_en || '',
      description: s.description || '',
      email: s.email || '',
      phone: s.phone || '',
      currency: s.currency || 'EGP',
      language: s.language || 'en',
      timezone: s.timezone || 'UTC',
      country: s.country || '',
      status: s.status || 'active'
    };
    const res = await seller.storeSettings(storeId.value);
    settings.value = res.data;
    await loadPos();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const loadPos = async () => {
  const res = await pos.supplier();
  posConn.value = res.data || null;
  if (posConn.value) {
    posForm.value.provider = posConn.value.provider || 'q-shop POS';
    posForm.value.api_url = posConn.value.api_url || '';
  }
};

// Connect: verify the key against the provider, then store it on this store.
const connectPos = async () => {
  if (!runPos()) return;
  posBusy.value = true;
  try {
    const res = await pos.connect({
      provider: posForm.value.provider || 'q-shop POS',
      api_url: posForm.value.api_url.trim(),
      api_key: posForm.value.api_key.trim()
    });
    posConn.value = res.data;
    posForm.value.api_key = ''; // don't keep the key in the form after connecting
    ui.success(t('posPage.connectedToast'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
  }
};

// Pull the supplier's catalog and upsert it into this store.
const importPos = async () => {
  importing.value = true;
  importSummary.value = null;
  try {
    const res = await pos.importProducts();
    posConn.value = res.data.connection;
    importSummary.value = res.data.summary;
    const s = res.data.summary;
    ui.success(t('posPage.importedToast', { created: s.created, updated: s.updated }));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    importing.value = false;
  }
};

const disconnectPos = async () => {
  if (!window.confirm(t('posPage.disconnectConfirm'))) return;
  posBusy.value = true;
  try {
    await pos.disconnect();
    posConn.value = null;
    posForm.value = { provider: 'q-shop POS', api_url: '', api_key: '' };
    importSummary.value = null;
    ui.success(t('posPage.disconnectedToast'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
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

    <!-- User preferences (language + theme) — always available, store-independent. -->
    <PreferencesCard class="mb-6" />

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
          <FormField v-model="profile.name_en" :label="$t('common.nameEn')" :hint="$t('common.nameEnHint')" />
          <div>
            <label class="label">{{ $t('common.description') }}</label>
            <textarea v-model="profile.description" rows="3" class="input"></textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <FormField v-model="profile.email" :label="$t('settingsPage.contactEmail')" type="email" />
            <FormField v-model="profile.phone" :label="$t('common.phone')" />
          </div>
          <div class="grid grid-cols-2 gap-4">
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
          <span class="chip border-0" :class="posConn?.is_connected ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'">
            <CheckCircle2 v-if="posConn?.is_connected" class="h-3.5 w-3.5" />
            {{ posConn?.is_connected ? $t('posPage.connected') : $t('posPage.notConnected') }}
          </span>
        </div>
        <p class="mb-4 text-sm text-muted">{{ $t('posPage.subtitle') }}</p>

        <!-- Connection form -->
        <div class="grid gap-4 sm:grid-cols-2">
          <FormField v-model="posForm.provider" :label="$t('posPage.provider')" placeholder="q-shop POS" :disabled="!canPos" />
          <FormField v-model="posForm.api_url" :label="$t('posPage.apiUrl')" :hint="$t('posPage.apiUrlHint')" placeholder="https://q-shop-cashier.deplois.net/api" :disabled="!canPos" :error="posErrors.api_url" @update:model-value="clearPos('api_url')" />
          <FormField v-model="posForm.api_key" :label="$t('posPage.apiKey')" type="password" :placeholder="posConn?.has_key ? '••••••••' : ''" :hint="posConn?.has_key ? $t('posPage.apiKeyStored') : ''" :disabled="!canPos" class="sm:col-span-2" :error="posErrors.api_key" @update:model-value="clearPos('api_key')" />
        </div>

        <!-- Connected summary -->
        <div v-if="posConn?.is_connected" class="mt-4 rounded-xl border border-slate-200 bg-lightbg/50 p-4 text-sm">
          <div class="flex flex-wrap gap-x-6 gap-y-1">
            <span v-if="posConn.remote_store_name"><span class="text-muted">{{ $t('posPage.remoteStore') }}:</span> <span class="font-medium">{{ posConn.remote_store_name }}</span></span>
            <span><span class="text-muted">{{ $t('posPage.productCount') }}:</span> <span class="font-medium">{{ posConn.remote_product_count }}</span></span>
            <span v-if="posConn.last_synced_at"><span class="text-muted">{{ $t('posPage.lastSync') }}:</span> {{ (posConn.last_synced_at || '').replace('T', ' ').slice(0, 16) }}</span>
          </div>
          <p v-if="importSummary" class="mt-2 text-emerald-700">{{ $t('posPage.importResult', { created: importSummary.created, updated: importSummary.updated, skipped: importSummary.skipped }) }}</p>
        </div>

        <!-- Actions -->
        <div v-if="canPos" class="mt-5 flex flex-wrap gap-2">
          <button v-if="!posConn?.is_connected" class="btn btn-primary btn-sm" :disabled="posBusy" @click="connectPos">
            <Spinner v-if="posBusy" :size="16" /><template v-else><Plug class="h-4 w-4" /> {{ $t('posPage.connect') }}</template>
          </button>
          <template v-else>
            <button class="btn btn-primary btn-sm" :disabled="importing || posBusy" @click="importPos">
              <Spinner v-if="importing" :size="16" /><template v-else><Download class="h-4 w-4" /> {{ importing ? $t('posPage.importing') : $t('posPage.import') }}</template>
            </button>
            <button class="btn btn-outline btn-sm" :disabled="posBusy" @click="connectPos">{{ $t('posPage.reconnect') }}</button>
            <button class="btn btn-ghost btn-sm text-secondary-600" :disabled="posBusy" @click="disconnectPos"><Unlink class="h-3.5 w-3.5" /> {{ $t('posPage.disconnect') }}</button>
          </template>
        </div>
        <p v-else class="mt-4 text-sm text-muted">{{ $t('posPage.noPermission') }}</p>
      </section>
    </div>
  </div>
</template>
