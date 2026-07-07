<script setup>
import { ref, computed, onMounted } from 'vue';
import { Store as StoreIcon, SlidersHorizontal, Cpu, CheckCircle2, Plug, Copy, RefreshCw, Unlink, KeyRound } from 'lucide-vue-next';
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
import { useValidation, url } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const storeId = ref(null);

const profile = ref(null);
const savingProfile = ref(false);

const settings = ref(null);
const savingSettings = ref(false);

// Cashier (POS) integration — a real per-store API key + optional sync webhook.
// The cashier deducts the shared warehouse stock on each in-store sale.
const posConn = ref(null); // the linked connection (or null when unlinked)
const posKey = ref(''); // plaintext key, shown ONCE right after link/rotate
const posBusy = ref(false);
const posWebhook = ref('');
const { errors: posErrors, run: runPos, clear: clearPos } = useValidation(
  () => ({ webhook_url: posWebhook.value }),
  { webhook_url: [url({ optional: true })] }
);
// Base URL the cashier calls (same origin as the SPA/API).
const apiBase = `${window.location.origin}/api/v1`;
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
  const res = await pos.connection();
  posConn.value = res.data || null;
  posWebhook.value = posConn.value?.webhook_url || '';
};

// Link the cashier: mints an API key, shown once for the seller to copy.
const linkPos = async () => {
  posBusy.value = true;
  try {
    const res = await pos.link({ name: 'Cashier' });
    posConn.value = res.data.connection;
    posKey.value = res.data.api_key;
    posWebhook.value = '';
    ui.success(t('posPage.linkedToast'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
  }
};

const rotatePos = async () => {
  posBusy.value = true;
  try {
    const res = await pos.rotate();
    posConn.value = res.data.connection;
    posKey.value = res.data.api_key;
    ui.success(t('posPage.rotatedToast'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
  }
};

const saveWebhook = async () => {
  if (!runPos()) return;
  posBusy.value = true;
  try {
    const res = await pos.update({ webhook_url: posWebhook.value.trim() });
    posConn.value = res.data;
    ui.success(t('posPage.webhookSaved'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
  }
};

const unlinkPos = async () => {
  if (!window.confirm(t('posPage.unlinkConfirm'))) return;
  posBusy.value = true;
  try {
    await pos.unlink();
    posConn.value = null;
    posKey.value = '';
    posWebhook.value = '';
    ui.success(t('posPage.unlinkedToast'));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    posBusy.value = false;
  }
};

const copy = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    ui.success(t('posPage.copied'));
  } catch {
    ui.error(t('posPage.copyFailed'));
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
          <span class="chip border-0" :class="posConn ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'">
            <CheckCircle2 v-if="posConn" class="h-3.5 w-3.5" />
            {{ posConn ? $t('posPage.linked') : $t('posPage.notLinked') }}
          </span>
        </div>
        <p class="mb-4 text-sm text-muted">{{ $t('posPage.subtitle') }}</p>

        <!-- Not linked yet -->
        <div v-if="!posConn">
          <button v-if="canPos" class="btn btn-primary btn-sm" :disabled="posBusy" @click="linkPos">
            <Spinner v-if="posBusy" :size="16" /><template v-else><Plug class="h-4 w-4" /> {{ $t('posPage.link') }}</template>
          </button>
          <p v-else class="text-sm text-muted">{{ $t('posPage.noPermission') }}</p>
        </div>

        <!-- Linked -->
        <div v-else class="space-y-5">
          <!-- Freshly minted key — shown once -->
          <div v-if="posKey" class="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p class="mb-2 flex items-center gap-2 text-sm font-medium text-amber-800"><KeyRound class="h-4 w-4" /> {{ $t('posPage.keyOnce') }}</p>
            <div class="flex items-center gap-2">
              <code class="flex-1 overflow-x-auto rounded-lg bg-white px-3 py-2 text-sm text-ink">{{ posKey }}</code>
              <button class="btn btn-outline btn-sm shrink-0" @click="copy(posKey)"><Copy class="h-3.5 w-3.5" /> {{ $t('posPage.copy') }}</button>
            </div>
          </div>
          <div v-else class="text-sm text-muted">
            {{ $t('posPage.currentKey') }}: <code class="rounded bg-lightbg px-2 py-0.5">{{ posConn.masked_key }}</code>
          </div>

          <!-- How the cashier connects -->
          <div class="rounded-xl border border-slate-200 bg-lightbg/50 p-4 text-sm">
            <p class="mb-2 font-medium">{{ $t('posPage.endpointsTitle') }}</p>
            <p class="mb-3 text-xs text-muted">{{ $t('posPage.headerHint') }} <code class="rounded bg-white px-1.5 py-0.5">X-POS-Key</code></p>
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="w-14 shrink-0 text-xs font-semibold text-emerald-600">POST</span>
                <code class="flex-1 overflow-x-auto text-xs text-ink">{{ apiBase }}/pos/sales/</code>
                <button class="btn btn-ghost btn-sm shrink-0" @click="copy(`${apiBase}/pos/sales/`)"><Copy class="h-3.5 w-3.5" /></button>
              </div>
              <div class="flex items-center gap-2">
                <span class="w-14 shrink-0 text-xs font-semibold text-primary-600">GET</span>
                <code class="flex-1 overflow-x-auto text-xs text-ink">{{ apiBase }}/pos/stock/</code>
                <button class="btn btn-ghost btn-sm shrink-0" @click="copy(`${apiBase}/pos/stock/`)"><Copy class="h-3.5 w-3.5" /></button>
              </div>
            </div>
          </div>

          <!-- Two-way sync webhook -->
          <div>
            <FormField v-model="posWebhook" :label="$t('posPage.webhook')" :hint="$t('posPage.webhookHint')" placeholder="https://cashier.example/stock-webhook" :disabled="!canPos" :error="posErrors.webhook_url" @update:model-value="clearPos('webhook_url')" />
            <button v-if="canPos" class="btn btn-outline btn-sm mt-2" :disabled="posBusy" @click="saveWebhook">{{ $t('posPage.saveWebhook') }}</button>
          </div>

          <!-- Actions -->
          <div v-if="canPos" class="flex flex-wrap gap-2 border-t border-slate-100 pt-4">
            <button class="btn btn-outline btn-sm" :disabled="posBusy" @click="rotatePos"><RefreshCw class="h-3.5 w-3.5" /> {{ $t('posPage.rotate') }}</button>
            <button class="btn btn-ghost btn-sm text-secondary-600" :disabled="posBusy" @click="unlinkPos"><Unlink class="h-3.5 w-3.5" /> {{ $t('posPage.unlink') }}</button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
