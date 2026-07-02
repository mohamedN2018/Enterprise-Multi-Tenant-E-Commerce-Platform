<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Truck, Building2, Send, PackageCheck, X, Trash2 } from 'lucide-vue-next';
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

const tab = ref('orders');
const loading = ref(true);
const suppliers = ref([]);
const orders = ref([]);
const warehouses = ref([]);
const variantOptions = ref([]);
const acting = ref(null);

const supplierMap = computed(() => Object.fromEntries(suppliers.value.map((s) => [s.id, s.name])));
const warehouseMap = computed(() => Object.fromEntries(warehouses.value.map((w) => [w.id, w.name])));

const supplierCols = [
  { key: 'name', label: 'Supplier', sortable: true },
  { key: 'email', label: 'Email' },
  { key: 'phone', label: 'Phone' },
  { key: 'is_active', label: 'Status' }
];
const poCols = [
  { key: 'number', label: 'PO', sortable: true },
  { key: 'supplier', label: 'Supplier' },
  { key: 'warehouse', label: 'Warehouse' },
  { key: 'subtotal', label: 'Subtotal', align: 'right', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'actions', label: '', align: 'right' }
];

const load = async () => {
  loading.value = true;
  try {
    const [sup, po, wh, prod] = await Promise.all([
      seller.suppliers(),
      seller.purchaseOrders(),
      seller.warehouses(),
      seller.products({ page_size: 100 })
    ]);
    suppliers.value = sup.data?.results || sup.data || [];
    orders.value = po.data?.results || po.data || [];
    warehouses.value = wh.data?.results || wh.data || [];
    const opts = [];
    (prod.data?.results || prod.data || []).forEach((p) => {
      (p.variants || []).forEach((v) => opts.push({ id: v.id, label: `${p.name}${v.name ? ` · ${v.name}` : ''} (${v.sku})` }));
    });
    variantOptions.value = opts;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

// Supplier create
const supModal = ref(false);
const supBusy = ref(false);
const supForm = ref({ name: '', code: '', email: '', phone: '', address: '' });
const createSupplier = async () => {
  supBusy.value = true;
  try {
    const payload = { ...supForm.value };
    if (!payload.code) delete payload.code;
    await seller.createSupplier(payload);
    ui.success('Supplier added.');
    supModal.value = false;
    supForm.value = { name: '', code: '', email: '', phone: '', address: '' };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    supBusy.value = false;
  }
};

// PO create
const poModal = ref(false);
const poBusy = ref(false);
const poForm = ref({ supplier_id: '', warehouse_id: '', expected_date: '', notes: '' });
const poLines = ref([]);
const openPO = () => {
  poForm.value = { supplier_id: suppliers.value[0]?.id || '', warehouse_id: warehouses.value[0]?.id || '', expected_date: '', notes: '' };
  poLines.value = [{ variant_id: variantOptions.value[0]?.id || '', quantity_ordered: 1, unit_cost: 0 }];
  poModal.value = true;
};
const addLine = () => poLines.value.push({ variant_id: variantOptions.value[0]?.id || '', quantity_ordered: 1, unit_cost: 0 });
const removeLine = (i) => poLines.value.splice(i, 1);
const createPO = async () => {
  poBusy.value = true;
  try {
    const payload = {
      supplier_id: poForm.value.supplier_id,
      warehouse_id: poForm.value.warehouse_id,
      notes: poForm.value.notes,
      lines: poLines.value.map((l) => ({ variant_id: l.variant_id, quantity_ordered: l.quantity_ordered, unit_cost: l.unit_cost }))
    };
    if (poForm.value.expected_date) payload.expected_date = poForm.value.expected_date;
    await seller.createPurchaseOrder(payload);
    ui.success('Purchase order created.');
    poModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    poBusy.value = false;
  }
};

const run = async (po, fn, msg) => {
  acting.value = po.id;
  try {
    await fn();
    ui.success(msg);
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    acting.value = null;
  }
};
const submitPO = (po) => run(po, () => seller.submitPurchaseOrder(po.id), 'PO submitted.');
const receivePO = (po) => run(po, () => seller.receivePurchaseOrder(po.id), 'Stock received.');
const cancelPO = (po) => run(po, () => seller.cancelPurchaseOrder(po.id), 'PO cancelled.');

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
  else loading.value = false;
});
</script>

<template>
  <div>
    <PageHeader title="Procurement" subtitle="Suppliers and purchase orders.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button v-if="tenant.canWrite && tab === 'suppliers'" class="btn btn-primary btn-sm" @click="supModal = true"><Plus class="h-4 w-4" /> Add supplier</button>
        <button v-if="tenant.canWrite && tab === 'orders'" class="btn btn-primary btn-sm" :disabled="!suppliers.length || !warehouses.length || !variantOptions.length" @click="openPO"><Plus class="h-4 w-4" /> New PO</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex gap-2">
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'orders' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'orders'"><Truck class="mr-1 inline h-4 w-4" /> Purchase orders</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'suppliers' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'suppliers'"><Building2 class="mr-1 inline h-4 w-4" /> Suppliers</button>
    </div>

    <DataTable v-if="tab === 'suppliers'" :columns="supplierCols" :rows="suppliers" :loading="loading" empty-title="No suppliers" empty-message="Add suppliers to create purchase orders.">
      <template #cell-name="{ row }"><span class="font-medium text-ink">{{ row.name }}</span></template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
    </DataTable>

    <DataTable v-else :columns="poCols" :rows="orders" :loading="loading" empty-title="No purchase orders" empty-message="Create a PO to restock from a supplier.">
      <template #cell-number="{ value }"><span class="font-medium text-ink">#{{ value }}</span></template>
      <template #cell-supplier="{ value }">{{ supplierMap[value] || '—' }}</template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || '—' }}</template>
      <template #cell-subtotal="{ row }">{{ row.subtotal }} {{ tenant.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite" class="flex justify-end gap-1">
          <button v-if="row.status === 'draft'" class="btn btn-ghost btn-sm text-primary-600" :disabled="acting === row.id" @click="submitPO(row)"><Send class="h-4 w-4" /> Submit</button>
          <button v-if="row.status === 'submitted'" class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="receivePO(row)"><PackageCheck class="h-4 w-4" /> Receive</button>
          <button v-if="['draft', 'submitted'].includes(row.status)" class="btn btn-ghost btn-sm text-secondary-500" :disabled="acting === row.id" @click="cancelPO(row)"><X class="h-4 w-4" /></button>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <!-- Supplier modal -->
    <Modal v-model="supModal" title="New supplier">
      <form id="sup-form" class="grid gap-4" @submit.prevent="createSupplier">
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="supForm.name" label="Name" required />
          <FormField v-model="supForm.code" label="Code" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="supForm.email" label="Email" type="email" />
          <FormField v-model="supForm.phone" label="Phone" />
        </div>
        <FormField v-model="supForm.address" label="Address" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="supModal = false">Cancel</button>
          <button form="sup-form" type="submit" class="btn btn-primary" :disabled="supBusy"><Spinner v-if="supBusy" :size="18" /><span v-else>Create</span></button>
        </div>
      </template>
    </Modal>

    <!-- PO modal -->
    <Modal v-model="poModal" title="New purchase order" size="lg">
      <form id="po-form" class="grid gap-4" @submit.prevent="createPO">
        <div class="grid gap-4 sm:grid-cols-3">
          <div>
            <label class="label">Supplier</label>
            <select v-model="poForm.supplier_id" class="input" required><option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option></select>
          </div>
          <div>
            <label class="label">Warehouse</label>
            <select v-model="poForm.warehouse_id" class="input" required><option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option></select>
          </div>
          <FormField v-model="poForm.expected_date" label="Expected date" type="date" />
        </div>

        <div>
          <div class="mb-2 flex items-center justify-between"><label class="label mb-0">Lines</label><button type="button" class="btn btn-ghost btn-sm" @click="addLine"><Plus class="h-4 w-4" /> Add line</button></div>
          <div v-for="(l, i) in poLines" :key="i" class="mb-2 grid grid-cols-[1fr_80px_100px_auto] items-end gap-2">
            <select v-model="l.variant_id" class="input"><option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option></select>
            <input v-model.number="l.quantity_ordered" type="number" min="1" class="input" placeholder="Qty" />
            <input v-model.number="l.unit_cost" type="number" step="0.01" class="input" placeholder="Cost" />
            <button type="button" class="grid h-9 w-9 place-items-center rounded-lg text-secondary-500 hover:bg-lightbg" :disabled="poLines.length <= 1" @click="removeLine(i)"><Trash2 class="h-4 w-4" /></button>
          </div>
        </div>
        <FormField v-model="poForm.notes" label="Notes" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="poModal = false">Cancel</button>
          <button form="po-form" type="submit" class="btn btn-primary" :disabled="poBusy"><Spinner v-if="poBusy" :size="18" /><span v-else>Create PO</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
