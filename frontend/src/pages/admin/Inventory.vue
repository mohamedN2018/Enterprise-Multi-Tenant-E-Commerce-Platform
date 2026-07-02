<script setup>
import { ref, computed, onMounted } from 'vue';
import { PackagePlus, Settings2, ArrowLeftRight, Warehouse as WarehouseIcon } from 'lucide-vue-next';
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
const tab = ref('stock');
const stock = ref([]);
const movements = ref([]);
const warehouses = ref([]);
const variantOptions = ref([]);
const variantMap = ref({});

const stockColumns = [
  { key: 'variant', label: 'Variant' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'quantity', label: 'On hand', align: 'right', sortable: true },
  { key: 'reserved_quantity', label: 'Reserved', align: 'right', sortable: true },
  { key: 'available_quantity', label: 'Available', align: 'right', sortable: true },
  { key: 'status', label: 'Status' }
];
const moveColumns = [
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'variant', label: 'Variant' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'movement_type', label: 'Type', sortable: true },
  { key: 'quantity_change', label: 'Change', align: 'right', sortable: true },
  { key: 'resulting_quantity', label: 'Resulting', align: 'right' }
];

const warehouseMap = computed(() => Object.fromEntries(warehouses.value.map((w) => [w.id, w.name])));

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
    const [st, wh, prod, mv] = await Promise.all([
      seller.stock(),
      seller.warehouses(),
      seller.products({ page_size: 100 }),
      seller.movements({ page_size: 30 })
    ]);
    stock.value = st.data?.results || st.data || [];
    warehouses.value = wh.data?.results || wh.data || [];
    buildVariantIndex(prod.data?.results || prod.data || []);
    movements.value = mv.data?.results || mv.data || [];
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

// --- Receive / adjust / transfer ------------------------------------------
const modal = ref(null); // 'receive' | 'adjust' | 'transfer'
const busy = ref(false);
const form = ref({ variant_id: '', warehouse_id: '', from_warehouse_id: '', to_warehouse_id: '', quantity: 0, note: '' });

const modalTitle = computed(() => ({ receive: 'Receive stock', adjust: 'Adjust stock', transfer: 'Transfer stock' }[modal.value] || ''));

const openModal = (kind) => {
  modal.value = kind;
  form.value = {
    variant_id: variantOptions.value[0]?.id || '',
    warehouse_id: warehouses.value[0]?.id || '',
    from_warehouse_id: warehouses.value[0]?.id || '',
    to_warehouse_id: warehouses.value[1]?.id || warehouses.value[0]?.id || '',
    quantity: kind === 'adjust' ? 0 : 1,
    note: ''
  };
};

const submit = async () => {
  busy.value = true;
  try {
    if (modal.value === 'receive') {
      await seller.receiveStock({ variant_id: form.value.variant_id, warehouse_id: form.value.warehouse_id, quantity: form.value.quantity, note: form.value.note });
    } else if (modal.value === 'adjust') {
      await seller.adjustStock({ variant_id: form.value.variant_id, warehouse_id: form.value.warehouse_id, quantity: form.value.quantity, note: form.value.note });
    } else {
      if (form.value.from_warehouse_id === form.value.to_warehouse_id) {
        ui.error('Choose two different warehouses.');
        busy.value = false;
        return;
      }
      await seller.transferStock({
        variant_id: form.value.variant_id,
        from_warehouse_id: form.value.from_warehouse_id,
        to_warehouse_id: form.value.to_warehouse_id,
        quantity: form.value.quantity,
        note: form.value.note
      });
    }
    ui.success('Inventory updated.');
    modal.value = null;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busy.value = false;
  }
};

// --- Warehouse creation ---------------------------------------------------
const whModal = ref(false);
const whBusy = ref(false);
const whForm = ref({ name: '', code: '', city: '', country: '', is_default: false });

const createWh = async () => {
  whBusy.value = true;
  try {
    await seller.createWarehouse(whForm.value);
    ui.success('Warehouse added.');
    whModal.value = false;
    whForm.value = { name: '', code: '', city: '', country: '', is_default: false };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    whBusy.value = false;
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
        <template v-if="tenant.canWrite">
          <button class="btn btn-outline btn-sm" @click="whModal = true"><WarehouseIcon class="h-4 w-4" /> New warehouse</button>
          <button class="btn btn-outline btn-sm" :disabled="warehouses.length < 2 || !variantOptions.length" @click="openModal('transfer')"><ArrowLeftRight class="h-4 w-4" /> Transfer</button>
          <button class="btn btn-outline btn-sm" :disabled="!variantOptions.length" @click="openModal('adjust')"><Settings2 class="h-4 w-4" /> Adjust</button>
          <button class="btn btn-primary btn-sm" :disabled="!variantOptions.length" @click="openModal('receive')"><PackagePlus class="h-4 w-4" /> Receive stock</button>
        </template>
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

    <!-- Tabs -->
    <div class="mb-4 flex gap-2">
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'stock' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'stock'">Stock levels</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'movements' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'movements'">Movements</button>
    </div>

    <!-- Stock -->
    <DataTable v-if="tab === 'stock'" :columns="stockColumns" :rows="stock" :loading="loading" empty-title="No stock records" empty-message="Receive stock to start tracking inventory.">
      <template #cell-variant="{ value }"><span class="font-medium text-ink">{{ variantMap[value] || shortId(value) }}</span></template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || shortId(value) }}</template>
      <template #cell-status="{ row }">
        <StatusBadge v-if="row.is_out_of_stock" status="failed" label="Out of stock" />
        <StatusBadge v-else-if="row.is_low_stock" status="pending" label="Low" />
        <StatusBadge v-else status="active" label="In stock" />
      </template>
    </DataTable>

    <!-- Movements ledger -->
    <DataTable v-else :columns="moveColumns" :rows="movements" :loading="loading" empty-title="No movements yet" empty-message="Stock receipts, adjustments and transfers will be logged here.">
      <template #cell-created_at="{ value }">{{ (value || '').replace('T', ' ').slice(0, 16) }}</template>
      <template #cell-variant="{ value }"><span class="font-medium text-ink">{{ variantMap[value] || shortId(value) }}</span></template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || shortId(value) }}</template>
      <template #cell-movement_type="{ value }"><span class="capitalize">{{ String(value).replace(/_/g, ' ') }}</span></template>
      <template #cell-quantity_change="{ value }">
        <span :class="Number(value) < 0 ? 'text-secondary-500' : 'text-emerald-600'">{{ Number(value) > 0 ? '+' : '' }}{{ value }}</span>
      </template>
    </DataTable>

    <!-- Modal -->
    <Modal :model-value="!!modal" :title="modalTitle" @update:model-value="modal = null">
      <form id="stock-form" class="grid gap-4" @submit.prevent="submit">
        <div>
          <label class="label">Variant</label>
          <select v-model="form.variant_id" class="input" required>
            <option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option>
          </select>
        </div>

        <template v-if="modal === 'transfer'">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label">From warehouse</label>
              <select v-model="form.from_warehouse_id" class="input" required>
                <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
            <div>
              <label class="label">To warehouse</label>
              <select v-model="form.to_warehouse_id" class="input" required>
                <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
              </select>
            </div>
          </div>
        </template>
        <div v-else>
          <label class="label">Warehouse</label>
          <select v-model="form.warehouse_id" class="input" required>
            <option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option>
          </select>
        </div>

        <FormField v-model.number="form.quantity" :label="modal === 'adjust' ? 'New on-hand quantity' : 'Quantity'" type="number" required />
        <FormField v-model="form.note" label="Note" placeholder="Optional" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="modal = null">Cancel</button>
          <button form="stock-form" type="submit" class="btn btn-primary" :disabled="busy">
            <Spinner v-if="busy" :size="18" /><span v-else>Confirm</span>
          </button>
        </div>
      </template>
    </Modal>

    <!-- New warehouse -->
    <Modal v-model="whModal" title="New warehouse">
      <form id="wh-form" class="grid gap-4" @submit.prevent="createWh">
        <FormField v-model="whForm.name" label="Name" placeholder="Main Warehouse" required />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="whForm.code" label="Code" placeholder="WH-2" required />
          <FormField v-model="whForm.city" label="City" />
        </div>
        <FormField v-model="whForm.country" label="Country (ISO-2)" maxlength="2" placeholder="US" />
        <label class="flex items-center gap-2 text-sm">
          <input v-model="whForm.is_default" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> Set as default warehouse
        </label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="whModal = false">Cancel</button>
          <button form="wh-form" type="submit" class="btn btn-primary" :disabled="whBusy">
            <Spinner v-if="whBusy" :size="18" /><span v-else>Create warehouse</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
