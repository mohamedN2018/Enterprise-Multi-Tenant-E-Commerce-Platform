<script setup>
import { ref, onMounted } from 'vue';
import { Plus, Percent, Coins, ArrowLeftRight } from 'lucide-vue-next';
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
const curForm = ref({ code: '', name: '', symbol: '', is_active: true });
const fxForm = ref({ base_code: '', target_code: '', rate: 1 });

const submit = async () => {
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
    ui.success('Saved.');
    modal.value = null;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busy.value = false;
  }
};

const zoneCols = [
  { key: 'name', label: 'Zone', sortable: true },
  { key: 'countries', label: 'Countries' },
  { key: 'is_default', label: 'Default' }
];
const curCols = [
  { key: 'code', label: 'Code', sortable: true },
  { key: 'name', label: 'Name', sortable: true },
  { key: 'symbol', label: 'Symbol' },
  { key: 'is_active', label: 'Status' }
];
const fxCols = [
  { key: 'base_code', label: 'Base', sortable: true },
  { key: 'target_code', label: 'Target', sortable: true },
  { key: 'rate', label: 'Rate', align: 'right', sortable: true },
  { key: 'created_at', label: 'Set' }
];

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
  else loading.value = false;
});
</script>

<template>
  <div>
    <PageHeader title="Finance" subtitle="Tax zones, currencies and exchange rates.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button v-if="tenant.canWrite && tab === 'tax'" class="btn btn-primary btn-sm" @click="modal = 'zone'"><Plus class="h-4 w-4" /> Tax zone</button>
        <button v-if="tenant.canWrite && tab === 'currency'" class="btn btn-primary btn-sm" @click="modal = 'currency'"><Plus class="h-4 w-4" /> Currency</button>
        <button v-if="tenant.canWrite && tab === 'fx'" class="btn btn-primary btn-sm" @click="modal = 'fx'"><Plus class="h-4 w-4" /> Exchange rate</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap gap-2">
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'tax' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'tax'"><Percent class="mr-1 inline h-4 w-4" /> Tax zones</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'currency' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'currency'"><Coins class="mr-1 inline h-4 w-4" /> Currencies</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'fx' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'fx'"><ArrowLeftRight class="mr-1 inline h-4 w-4" /> Exchange rates</button>
    </div>

    <DataTable v-if="tab === 'tax'" :columns="zoneCols" :rows="zones" :loading="loading" empty-title="No tax zones" empty-message="Define tax zones to apply taxes by country.">
      <template #cell-name="{ row }"><span class="font-medium text-ink">{{ row.name }}</span></template>
      <template #cell-countries="{ value }"><span class="text-xs text-muted">{{ (value || []).join(', ') || 'All' }}</span></template>
      <template #cell-is_default="{ value }"><StatusBadge v-if="value" status="active" label="Default" /><span v-else class="text-xs text-muted">—</span></template>
    </DataTable>

    <DataTable v-else-if="tab === 'currency'" :columns="curCols" :rows="currencies" :loading="loading" empty-title="No currencies" empty-message="Add currencies your store supports.">
      <template #cell-code="{ value }"><span class="font-mono font-semibold">{{ value }}</span></template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
    </DataTable>

    <DataTable v-else :columns="fxCols" :rows="rates" :loading="loading" empty-title="No exchange rates" empty-message="Add conversion rates between currencies.">
      <template #cell-base_code="{ value }"><span class="font-mono">{{ value }}</span></template>
      <template #cell-target_code="{ value }"><span class="font-mono">{{ value }}</span></template>
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
    </DataTable>

    <Modal :model-value="!!modal" :title="{ zone: 'New tax zone', currency: 'New currency', fx: 'New exchange rate' }[modal] || ''" @update:model-value="modal = null">
      <form v-if="modal === 'zone'" id="fin-form" class="grid gap-4" @submit.prevent="submit">
        <FormField v-model="zoneForm.name" label="Zone name" placeholder="EU" required />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="zoneForm.code" label="Code" />
          <FormField v-model="zoneForm.countries" label="Countries (comma)" placeholder="DE, FR" />
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="zoneForm.is_default" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> Default zone</label>
      </form>
      <form v-else-if="modal === 'currency'" id="fin-form" class="grid gap-4" @submit.prevent="submit">
        <div class="grid grid-cols-3 gap-4">
          <FormField v-model="curForm.code" label="Code" placeholder="EUR" maxlength="3" required />
          <FormField v-model="curForm.symbol" label="Symbol" placeholder="€" />
          <FormField v-model="curForm.name" label="Name" placeholder="Euro" required />
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="curForm.is_active" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> Active</label>
      </form>
      <form v-else id="fin-form" class="grid gap-4" @submit.prevent="submit">
        <div class="grid grid-cols-3 gap-4">
          <FormField v-model="fxForm.base_code" label="Base" placeholder="USD" maxlength="3" required />
          <FormField v-model="fxForm.target_code" label="Target" placeholder="EUR" maxlength="3" required />
          <FormField v-model.number="fxForm.rate" label="Rate" type="number" step="0.0001" required />
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="modal = null">Cancel</button>
          <button form="fin-form" type="submit" class="btn btn-primary" :disabled="busy"><Spinner v-if="busy" :size="18" /><span v-else>Create</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
