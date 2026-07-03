<script setup>
import { ref, onMounted } from 'vue';
import { Store as StoreIcon, SlidersHorizontal } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';

const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const storeId = ref(null);

const profile = ref(null);
const savingProfile = ref(false);

const settings = ref(null);
const savingSettings = ref(false);

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
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
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
    </div>
  </div>
</template>
