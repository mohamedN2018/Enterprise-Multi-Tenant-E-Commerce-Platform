<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Percent, Coins, ArrowLeftRight } from 'lucide-vue-next';
import { t } from '@/i18n';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { useValidation, required, positive } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const tab = ref('tax');
const loading = ref(true);
const zones = ref([]);
const currencies = ref([]);
const rates = ref([]);

const load = async () => {
  loading.value = true;
  try {
    const [z, c, r] = await Promise.all([
      seller.taxZones(),
      seller.currencies(),
      seller.exchangeRates()
    ]);
    zones.value = z.data?.results || z.data || [];
    currencies.value = c.data?.results || c.data || [];
    rates.value = r.data?.results || r.data || [];
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const modal = ref(null); // 'zone' | 'currency' | 'fx'
const busy = ref(false);
const zoneForm = ref({ name: '', code: '', countries: '', is_default: false });
const { errors: zoneErrors, run: runZone, clear: clearZone } = useValidation(() => zoneForm.value, { name: [required()] });
const curForm = ref({ code: '', name: '', symbol: '', is_active: true });
const { errors: curErrors, run: runCur, clear: clearCur } = useValidation(() => curForm.value, { code: [required()], name: [required()] });
const fxForm = ref({ base_code: '', target_code: '', rate: 1 });
const { errors: fxErrors, run: runFx, clear: clearFx } = useValidation(() => fxForm.value, { base_code: [required()], target_code: [required()], rate: [positive()] });

const submit = async () => {
  if (modal.value === 'zone') {
    if (!runZone()) return;
  } else if (modal.value === 'currency') {
    if (!runCur()) return;
  } else {
    if (!runFx()) return;
  }
  busy.value = true;
  try {
    if (modal.value === 'zone') {
      await seller.createTaxZone({
        name: zoneForm.value.name,
        code: zoneForm.value.code || undefined,
        countries: zoneForm.value.countries ? zoneForm.value.countries.split(',').map((x) => x.trim().toUpperCase()).filter(Boolean) : [],
        is_default: zoneForm.value.is_default
      });
    } else if (modal.value === 'currency') {
      await seller.createCurrency(curForm.value);
    } else {
      await seller.createExchangeRate({
        base_code: fxForm.value.base_code.toUpperCase(),
        target_code: fxForm.value.target_code.toUpperCase(),
        rate: fxForm.value.rate
      });
    }
    ui.success(t('financePage.saved'));
    modal.value = null;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busy.value = false;
  }
};

const zoneCols = computed(() => [
  { key: 'name', label: t('financePage.zone'), sortable: true },
  { key: 'countries', label: t('financePage.countries') },
  { key: 'is_default', label: t('financePage.default') }
]);
const curCols = computed(() => [
  { key: 'code', label: t('financePage.code'), sortable: true },
  { key: 'name', label: t('common.name'), sortable: true },
  { key: 'symbol', label: t('financePage.symbol') },
  { key: 'is_active', label: t('common.status') }
]);
const fxCols = computed(() => [
  { key: 'base_code', label: t('financePage.base'), sortable: true },
  { key: 'target_code', label: t('financePage.target'), sortable: true },
  { key: 'rate', label: t('financePage.rate'), align: 'right', sortable: true },
  { key: 'created_at', label: t('financePage.set') }
]);

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
  else loading.value = false;
});
</script>

<template>
  <div>
    <PageHeader :title="$t('financePage.title')" :subtitle="$t('financePage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button v-if="tenant.canWrite && tab === 'tax'" class="btn btn-primary btn-sm" @click="modal = 'zone'"><Plus class="h-4 w-4" /> {{ $t('financePage.taxZone') }}</button>
        <button v-if="tenant.canWrite && tab === 'currency'" class="btn btn-primary btn-sm" @click="modal = 'currency'"><Plus class="h-4 w-4" /> {{ $t('financePage.currency') }}</button>
        <button v-if="tenant.canWrite && tab === 'fx'" class="btn btn-primary btn-sm" @click="modal = 'fx'"><Plus class="h-4 w-4" /> {{ $t('financePage.exchangeRate') }}</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap gap-2">
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'tax' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'tax'"><Percent class="me-1 inline h-4 w-4" /> {{ $t('financePage.taxZones') }}</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'currency' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'currency'"><Coins class="me-1 inline h-4 w-4" /> {{ $t('financePage.currencies') }}</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'fx' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'fx'"><ArrowLeftRight class="me-1 inline h-4 w-4" /> {{ $t('financePage.exchangeRates') }}</button>
    </div>

    <DataTable v-if="tab === 'tax'" :columns="zoneCols" :rows="zones" :loading="loading" :empty-title="$t('financePage.noZones')" :empty-message="$t('financePage.noZonesMsg')">
      <template #cell-name="{ row }"><span class="font-medium text-ink">{{ row.name }}</span></template>
      <template #cell-countries="{ value }"><span class="text-xs text-muted">{{ (value || []).join(', ') || $t('common.all') }}</span></template>
      <template #cell-is_default="{ value }"><StatusBadge v-if="value" status="active" :label="$t('financePage.default')" /><span v-else class="text-xs text-muted">—</span></template>
    </DataTable>

    <DataTable v-else-if="tab === 'currency'" :columns="curCols" :rows="currencies" :loading="loading" :empty-title="$t('financePage.noCurrencies')" :empty-message="$t('financePage.noCurrenciesMsg')">
      <template #cell-code="{ value }"><span class="font-mono font-semibold">{{ value }}</span></template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
    </DataTable>

    <DataTable v-else :columns="fxCols" :rows="rates" :loading="loading" :empty-title="$t('financePage.noRates')" :empty-message="$t('financePage.noRatesMsg')">
      <template #cell-base_code="{ value }"><span class="font-mono">{{ value }}</span></template>
      <template #cell-target_code="{ value }"><span class="font-mono">{{ value }}</span></template>
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
    </DataTable>

    <Modal :model-value="!!modal" :title="{ zone: $t('financePage.newZone'), currency: $t('financePage.newCurrency'), fx: $t('financePage.newFx') }[modal] || ''" @update:model-value="modal = null">
      <form v-if="modal === 'zone'" id="fin-form" class="grid gap-4" novalidate @submit.prevent="submit">
        <FormField v-model="zoneForm.name" :label="$t('financePage.zoneName')" placeholder="EU" required :error="zoneErrors.name" @update:model-value="clearZone('name')" />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="zoneForm.code" :label="$t('financePage.code')" />
          <FormField v-model="zoneForm.countries" :label="$t('financePage.countriesComma')" placeholder="DE, FR" />
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="zoneForm.is_default" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('financePage.defaultZone') }}</label>
      </form>
      <form v-else-if="modal === 'currency'" id="fin-form" class="grid gap-4" novalidate @submit.prevent="submit">
        <div class="grid grid-cols-3 gap-4">
          <FormField v-model="curForm.code" :label="$t('financePage.code')" placeholder="EUR" maxlength="3" required :error="curErrors.code" @update:model-value="clearCur('code')" />
          <FormField v-model="curForm.symbol" :label="$t('financePage.symbol')" placeholder="€" />
          <FormField v-model="curForm.name" :label="$t('common.name')" placeholder="Euro" required :error="curErrors.name" @update:model-value="clearCur('name')" />
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="curForm.is_active" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('common.active') }}</label>
      </form>
      <form v-else id="fin-form" class="grid gap-4" novalidate @submit.prevent="submit">
        <div class="grid grid-cols-3 gap-4">
          <FormField v-model="fxForm.base_code" :label="$t('financePage.base')" placeholder="USD" maxlength="3" required :error="fxErrors.base_code" @update:model-value="clearFx('base_code')" />
          <FormField v-model="fxForm.target_code" :label="$t('financePage.target')" placeholder="EUR" maxlength="3" required :error="fxErrors.target_code" @update:model-value="clearFx('target_code')" />
          <FormField v-model.number="fxForm.rate" :label="$t('financePage.rate')" type="number" step="0.0001" required :error="fxErrors.rate" @update:model-value="clearFx('rate')" />
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="modal = null">{{ $t('common.cancel') }}</button>
          <button form="fin-form" type="submit" class="btn btn-primary" :disabled="busy"><Spinner v-if="busy" :size="18" /><span v-else>{{ $t('common.create') }}</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
