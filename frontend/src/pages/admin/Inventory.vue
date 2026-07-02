<script setup>
import { ref, computed, onMounted } from 'vue';
import { PackagePlus, Settings2, Warehouse as WarehouseIcon } from 'lucide-vue-next';
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

const loading = ref(true);
const stock = ref([]);
const warehouses = ref([]);
const variantOptions = ref([]);
const variantMap = ref({});

const columns = [
  { key: 'variant', label: 'Variant' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'quantity', label: 'On hand', align: 'right' },
  { key: 'reserved_quantity', label: 'Reserved', align: 'right' },
  { key: 'available_quantity', label: 'Available', align: 'right' },
  { key: 'status', label: 'Status' }
];

const warehouseMap = computed(() =>
  Object.fromEntries(warehouses.value.map((w) => [w.id, w.name]))
);

const buildVariantIndex = (products) => {
  const opts = [];
  const map = {};
  products.forEach((p) => {
    (p.variants || []).forEach((v) => {
      const label = `${p.name}${v.name ? ` · ${v.name}` : ''} (${v.sku})`;
      opts.push({ id: v.id, label });
      map[v.id] = label;
    });
  });
  variantOptions.value = opts;
  variantMap.value = map;
};

const load = async () => {
  loading.value = true;
  try {
    const [st, wh, prod] = await Promise.all([
      seller.stock(),
      seller.warehouses(),
      seller.products({ page_size: 100 })
    ]);
    stock.value = st.data?.results || st.data || [];
    warehouses.value = wh.data?.results || wh.data || [];
    buildVariantIndex(prod.data?.results || prod.data || []);
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

// --- Receive / adjust ------------------------------------------------------
const modal = ref(null); // 'receive' | 'adjust'
const busy = ref(false);
const form = ref({ variant_id: '', warehouse_id: '', quantity: 0, note: '' });

const openModal = (kind) => {
  modal.value = kind;
  form.value = {
    variant_id: variantOptions.value[0]?.id || '',
    warehouse_id: warehouses.value[0]?.id || '',
    quantity: kind === 'receive' ? 1 : 0,
    note: ''
  };
};

const submit = async () => {
  busy.value = true;
  try {
    if (modal.value === 'receive') await seller.receiveStock(form.value);
    else await seller.adjustStock(form.value);
    ui.success(modal.value === 'receive' ? 'Stock received.' : 'Stock adjusted.');
    modal.value = null;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busy.value = false;
  }
};

const shortId = (id) => (id ? `${id}`.slice(0, 8) : '—');

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
  else loading.value = false;
});
</script>

<template>
  <div>
    <PageHeader title="Inventory" subtitle="Track stock across warehouses.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button v-if="tenant.canWrite" class="btn btn-outline btn-sm" :disabled="!variantOptions.length" @click="openModal('adjust')">
          <Settings2 class="h-4 w-4" /> Adjust
        </button>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" :disabled="!variantOptions.length" @click="openModal('receive')">
          <PackagePlus class="h-4 w-4" /> Receive stock
        </button>
      </template>
    </PageHeader>

    <div v-if="warehouses.length" class="mb-4 flex flex-wrap gap-3">
      <div v-for="w in warehouses" :key="w.id" class="card flex items-center gap-2 px-4 py-2 text-sm">
        <WarehouseIcon class="h-4 w-4 text-primary-600" />
        <span class="font-medium">{{ w.name }}</span>
        <span class="text-slate-400">{{ w.code }}</span>
        <StatusBadge v-if="w.is_default" status="active" label="Default" />
      </div>
    </div>

    <DataTable :columns="columns" :rows="stock" :loading="loading" empty-title="No stock records" empty-message="Receive stock to start tracking inventory.">
      <template #cell-variant="{ value }">
        <span class="font-medium text-ink">{{ variantMap[value] || shortId(value) }}</span>
      </template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || shortId(value) }}</template>
      <template #cell-status="{ row }">
        <StatusBadge v-if="row.is_out_of_stock" status="failed" label="Out of stock" />
        <StatusBadge v-else-if="row.is_low_stock" status="pending" label="Low" />
        <StatusBadge v-else status="active" label="In stock" />
      </template>
    </DataTable>

    <Modal :model-value="!!modal" :title="modal === 'receive' ? 'Receive stock' : 'Adjust stock'" @update:model-value="modal = null">
      <form id="stock-form" class="grid gap-4" @submit.prevent="submit">
        <div>
          <label class="label">Variant</label>
          <select v-model="form.variant_id" class="input" required>
            <option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option>
          </select>
        </div>
        <div>
          <label class="label">Warehouse</label>
          <select v-model="form.warehouse_id" class="input" required>
            <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </div>
        <FormField v-model.number="form.quantity" :label="modal === 'receive' ? 'Quantity to add' : 'New on-hand quantity'" type="number" required />
        <FormField v-model="form.note" label="Note" placeholder="Optional" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="modal = null">Cancel</button>
          <button form="stock-form" type="submit" class="btn btn-primary" :disabled="busy">
            <Spinner v-if="busy" :size="18" /><span v-else>{{ modal === 'receive' ? 'Receive' : 'Adjust' }}</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
