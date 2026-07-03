<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Truck, Building2, Send, PackageCheck, X, Trash2, Boxes, Hash, Factory, Wrench } from 'lucide-vue-next';
import { t } from '@/i18n';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
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
const batches = ref([]);
const serials = ref([]);
const boms = ref([]);
const workorders = ref([]);
const acting = ref(null);

const supplierMap = computed(() => Object.fromEntries(suppliers.value.map((s) => [s.id, s.name])));
const warehouseMap = computed(() => Object.fromEntries(warehouses.value.map((w) => [w.id, w.name])));
const variantMap = computed(() => Object.fromEntries(variantOptions.value.map((v) => [v.id, v.label])));
const bomMap = computed(() => Object.fromEntries(boms.value.map((b) => [b.id, b.name])));

const TABS = computed(() => [
  { key: 'orders', label: t('procurementPage.purchaseOrders'), icon: Truck },
  { key: 'suppliers', label: t('procurementPage.suppliers'), icon: Building2 },
  { key: 'batches', label: t('procurementPage.batches'), icon: Boxes },
  { key: 'serials', label: t('procurementPage.serials'), icon: Hash },
  { key: 'boms', label: t('procurementPage.billsOfMaterials'), icon: Factory },
  { key: 'workorders', label: t('procurementPage.workOrders'), icon: Wrench }
]);

const supplierCols = computed(() => [
  { key: 'name', label: t('procurementPage.supplier'), sortable: true },
  { key: 'email', label: t('common.email') },
  { key: 'phone', label: t('common.phone') },
  { key: 'is_active', label: t('common.status') }
]);
const poCols = computed(() => [
  { key: 'number', label: t('procurementPage.po'), sortable: true },
  { key: 'supplier', label: t('procurementPage.supplier') },
  { key: 'warehouse', label: t('procurementPage.warehouse') },
  { key: 'subtotal', label: t('common.subtotal'), align: 'right', sortable: true },
  { key: 'status', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);
const batchCols = computed(() => [
  { key: 'batch_number', label: t('procurementPage.batch'), sortable: true },
  { key: 'variant', label: t('procurementPage.variant') },
  { key: 'warehouse', label: t('procurementPage.warehouse') },
  { key: 'quantity', label: t('procurementPage.qty'), align: 'right', sortable: true },
  { key: 'expiry_date', label: t('procurementPage.expiry') }
]);
const serialCols = computed(() => [
  { key: 'serial', label: t('procurementPage.serial'), sortable: true },
  { key: 'variant', label: t('procurementPage.variant') },
  { key: 'warehouse', label: t('procurementPage.warehouse') },
  { key: 'status', label: t('common.status'), sortable: true }
]);
const woCols = computed(() => [
  { key: 'number', label: t('procurementPage.wo'), sortable: true },
  { key: 'bom', label: t('procurementPage.bom') },
  { key: 'warehouse', label: t('procurementPage.warehouse') },
  { key: 'quantity', label: t('procurementPage.qty'), align: 'right', sortable: true },
  { key: 'status', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

const load = async () => {
  loading.value = true;
  try {
    const [sup, po, wh, prod, bat, ser, bm, wo] = await Promise.all([
      seller.suppliers(),
      seller.purchaseOrders(),
      seller.warehouses(),
      seller.products({ page_size: 100 }),
      seller.stockBatches().catch(() => ({ data: [] })),
      seller.serials().catch(() => ({ data: [] })),
      seller.boms().catch(() => ({ data: [] })),
      seller.workOrders().catch(() => ({ data: [] }))
    ]);
    suppliers.value = sup.data?.results || sup.data || [];
    orders.value = po.data?.results || po.data || [];
    warehouses.value = wh.data?.results || wh.data || [];
    const opts = [];
    (prod.data?.results || prod.data || []).forEach((p) => {
      (p.variants || []).forEach((v) => opts.push({ id: v.id, label: `${p.name}${v.name ? ` · ${v.name}` : ''} (${v.sku})` }));
    });
    variantOptions.value = opts;
    batches.value = bat.data?.results || bat.data || [];
    serials.value = ser.data?.results || ser.data || [];
    boms.value = bm.data?.results || bm.data || [];
    workorders.value = wo.data?.results || wo.data || [];
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

// --- Supplier create ---
const supModal = ref(false);
const supBusy = ref(false);
const supForm = ref({ name: '', code: '', email: '', phone: '', address: '' });
const createSupplier = async () => {
  supBusy.value = true;
  try {
    const payload = { ...supForm.value };
    if (!payload.code) delete payload.code;
    await seller.createSupplier(payload);
    ui.success(t('procurementPage.supplierAdded'));
    supModal.value = false;
    supForm.value = { name: '', code: '', email: '', phone: '', address: '' };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    supBusy.value = false;
  }
};

// --- PO create ---
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
    const payload = { supplier_id: poForm.value.supplier_id, warehouse_id: poForm.value.warehouse_id, notes: poForm.value.notes, lines: poLines.value };
    if (poForm.value.expected_date) payload.expected_date = poForm.value.expected_date;
    await seller.createPurchaseOrder(payload);
    ui.success(t('procurementPage.poCreated'));
    poModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    poBusy.value = false;
  }
};

// --- Serials register ---
const serModal = ref(false);
const serBusy = ref(false);
const serForm = ref({ variant_id: '', warehouse_id: '', serials: '' });
const openSerials = () => {
  serForm.value = { variant_id: variantOptions.value[0]?.id || '', warehouse_id: warehouses.value[0]?.id || '', serials: '' };
  serModal.value = true;
};
const registerSerials = async () => {
  serBusy.value = true;
  try {
    await seller.registerSerials({
      variant_id: serForm.value.variant_id,
      warehouse_id: serForm.value.warehouse_id,
      serials: serForm.value.serials.split(/[\n,]/).map((s) => s.trim()).filter(Boolean)
    });
    ui.success(t('procurementPage.serialsRegistered'));
    serModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    serBusy.value = false;
  }
};

// --- BOM create + component ---
const bomModal = ref(false);
const bomBusy = ref(false);
const bomForm = ref({ output_variant_id: '', name: '' });
const openBom = () => {
  bomForm.value = { output_variant_id: variantOptions.value[0]?.id || '', name: '' };
  bomModal.value = true;
};
const createBom = async () => {
  bomBusy.value = true;
  try {
    await seller.createBom(bomForm.value);
    ui.success(t('procurementPage.bomCreated'));
    bomModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    bomBusy.value = false;
  }
};
const compModal = ref(false);
const compBusy = ref(false);
const compBom = ref(null);
const compForm = ref({ component_variant_id: '', quantity: 1 });
const openComp = (bom) => {
  compBom.value = bom;
  compForm.value = { component_variant_id: variantOptions.value[0]?.id || '', quantity: 1 };
  compModal.value = true;
};
const addComponent = async () => {
  compBusy.value = true;
  try {
    await seller.addBomComponent(compBom.value.id, compForm.value);
    ui.success(t('procurementPage.componentAdded'));
    compModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    compBusy.value = false;
  }
};

// --- Work order create + actions ---
const woModal = ref(false);
const woBusy = ref(false);
const woForm = ref({ bom_id: '', warehouse_id: '', quantity: 1 });
const openWo = () => {
  woForm.value = { bom_id: boms.value[0]?.id || '', warehouse_id: warehouses.value[0]?.id || '', quantity: 1 };
  woModal.value = true;
};
const createWo = async () => {
  woBusy.value = true;
  try {
    await seller.createWorkOrder(woForm.value);
    ui.success(t('procurementPage.woCreated'));
    woModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    woBusy.value = false;
  }
};

const run = async (item, fn, msg) => {
  acting.value = item.id;
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
const submitPO = (po) => run(po, () => seller.submitPurchaseOrder(po.id), t('procurementPage.poSubmitted'));
const receivePO = (po) => run(po, () => seller.receivePurchaseOrder(po.id), t('procurementPage.stockReceived'));
const cancelPO = (po) => run(po, () => seller.cancelPurchaseOrder(po.id), t('procurementPage.poCancelled'));
const completeWo = (wo) => run(wo, () => seller.completeWorkOrder(wo.id), t('procurementPage.woCompleted'));
const cancelWo = (wo) => run(wo, () => seller.cancelWorkOrder(wo.id), t('procurementPage.woCancelled'));

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
  else loading.value = false;
});
</script>

<template>
  <div>
    <PageHeader :title="$t('procurementPage.title')" :subtitle="$t('procurementPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button v-if="tenant.canWrite && tab === 'suppliers'" class="btn btn-primary btn-sm" @click="supModal = true"><Plus class="h-4 w-4" /> {{ $t('procurementPage.addSupplier') }}</button>
        <button v-if="tenant.canWrite && tab === 'orders'" class="btn btn-primary btn-sm" :disabled="!suppliers.length || !warehouses.length || !variantOptions.length" @click="openPO"><Plus class="h-4 w-4" /> {{ $t('procurementPage.newPo') }}</button>
        <button v-if="tenant.canWrite && tab === 'serials'" class="btn btn-primary btn-sm" :disabled="!variantOptions.length || !warehouses.length" @click="openSerials"><Plus class="h-4 w-4" /> {{ $t('procurementPage.registerSerials') }}</button>
        <button v-if="tenant.canWrite && tab === 'boms'" class="btn btn-primary btn-sm" :disabled="!variantOptions.length" @click="openBom"><Plus class="h-4 w-4" /> {{ $t('procurementPage.newBom') }}</button>
        <button v-if="tenant.canWrite && tab === 'workorders'" class="btn btn-primary btn-sm" :disabled="!boms.length || !warehouses.length" @click="openWo"><Plus class="h-4 w-4" /> {{ $t('procurementPage.newWorkOrder') }}</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap gap-2">
      <button v-for="tabItem in TABS" :key="tabItem.key" class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === tabItem.key ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = tabItem.key">
        <component :is="tabItem.icon" class="me-1 inline h-4 w-4" /> {{ tabItem.label }}
      </button>
    </div>

    <!-- Purchase orders -->
    <DataTable v-if="tab === 'orders'" :columns="poCols" :rows="orders" :loading="loading" :empty-title="$t('procurementPage.noPurchaseOrders')" :empty-message="$t('procurementPage.noPurchaseOrdersMsg')">
      <template #cell-number="{ value }"><span class="font-medium text-ink">#{{ value }}</span></template>
      <template #cell-supplier="{ value }">{{ supplierMap[value] || '—' }}</template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || '—' }}</template>
      <template #cell-subtotal="{ row }">{{ row.subtotal }} {{ tenant.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite" class="flex justify-end gap-1">
          <button v-if="row.status === 'draft'" class="btn btn-ghost btn-sm text-primary-600" :disabled="acting === row.id" @click="submitPO(row)"><Send class="h-4 w-4" /> {{ $t('common.submit') }}</button>
          <button v-if="row.status === 'submitted'" class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="receivePO(row)"><PackageCheck class="h-4 w-4" /> {{ $t('procurementPage.receive') }}</button>
          <button v-if="['draft', 'submitted'].includes(row.status)" class="btn btn-ghost btn-sm text-secondary-500" :disabled="acting === row.id" @click="cancelPO(row)"><X class="h-4 w-4" /></button>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <!-- Suppliers -->
    <DataTable v-else-if="tab === 'suppliers'" :columns="supplierCols" :rows="suppliers" :loading="loading" :empty-title="$t('procurementPage.noSuppliers')" :empty-message="$t('procurementPage.noSuppliersMsg')">
      <template #cell-name="{ row }"><span class="font-medium text-ink">{{ row.name }}</span></template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
    </DataTable>

    <!-- Batches -->
    <DataTable v-else-if="tab === 'batches'" :columns="batchCols" :rows="batches" :loading="loading" :empty-title="$t('procurementPage.noBatches')" :empty-message="$t('procurementPage.noBatchesMsg')">
      <template #cell-variant="{ value }"><span class="font-medium text-ink">{{ variantMap[value] || String(value).slice(0, 8) }}</span></template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || '—' }}</template>
      <template #cell-expiry_date="{ value }">{{ value || '—' }}</template>
    </DataTable>

    <!-- Serials -->
    <DataTable v-else-if="tab === 'serials'" :columns="serialCols" :rows="serials" :loading="loading" :empty-title="$t('procurementPage.noSerials')" :empty-message="$t('procurementPage.noSerialsMsg')">
      <template #cell-serial="{ value }"><span class="font-mono">{{ value }}</span></template>
      <template #cell-variant="{ value }"><span class="font-medium text-ink">{{ variantMap[value] || String(value).slice(0, 8) }}</span></template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || '—' }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
    </DataTable>

    <!-- BOMs -->
    <div v-else-if="tab === 'boms'">
      <div v-if="loading" class="flex min-h-[20vh] items-center justify-center"><Spinner :size="26" :label="$t('common.loading')" /></div>
      <div v-else-if="boms.length" class="grid gap-5 lg:grid-cols-2">
        <div v-for="b in boms" :key="b.id" class="card p-5">
          <div class="mb-3 flex items-start justify-between">
            <div>
              <h3 class="flex items-center gap-2 font-heading text-lg font-bold"><Factory class="h-5 w-5 text-primary-600" /> {{ b.name }}</h3>
              <p class="text-xs text-muted">{{ $t('procurementPage.output') }}: {{ variantMap[b.output_variant] || String(b.output_variant).slice(0, 8) }}</p>
            </div>
            <StatusBadge :status="b.is_active ? 'active' : 'inactive'" />
          </div>
          <ul class="space-y-1">
            <li v-for="c in b.components || []" :key="c.id" class="flex justify-between rounded-lg bg-lightbg px-3 py-1.5 text-sm">
              <span>{{ variantMap[c.component_variant] || String(c.component_variant).slice(0, 8) }}</span>
              <span class="text-muted">× {{ c.quantity }}</span>
            </li>
            <li v-if="!(b.components || []).length" class="text-sm text-muted">{{ $t('procurementPage.noComponents') }}</li>
          </ul>
          <button v-if="tenant.canWrite" class="btn btn-outline btn-sm mt-4" @click="openComp(b)"><Plus class="h-4 w-4" /> {{ $t('procurementPage.addComponent') }}</button>
        </div>
      </div>
      <EmptyState v-else :icon="Factory" :title="$t('procurementPage.noBoms')" :message="$t('procurementPage.noBomsMsg')" />
    </div>

    <!-- Work orders -->
    <DataTable v-else :columns="woCols" :rows="workorders" :loading="loading" :empty-title="$t('procurementPage.noWorkOrders')" :empty-message="$t('procurementPage.noWorkOrdersMsg')">
      <template #cell-number="{ value }"><span class="font-medium text-ink">#{{ value }}</span></template>
      <template #cell-bom="{ value }">{{ bomMap[value] || '—' }}</template>
      <template #cell-warehouse="{ value }">{{ warehouseMap[value] || '—' }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite" class="flex justify-end gap-1">
          <button v-if="['draft', 'pending', 'in_progress'].includes(row.status)" class="btn btn-ghost btn-sm text-emerald-600" :disabled="acting === row.id" @click="completeWo(row)"><PackageCheck class="h-4 w-4" /> {{ $t('procurementPage.complete') }}</button>
          <button v-if="row.status !== 'completed' && row.status !== 'cancelled'" class="btn btn-ghost btn-sm text-secondary-500" :disabled="acting === row.id" @click="cancelWo(row)"><X class="h-4 w-4" /></button>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <!-- Supplier modal -->
    <Modal v-model="supModal" :title="$t('procurementPage.newSupplier')">
      <form id="sup-form" class="grid gap-4" @submit.prevent="createSupplier">
        <div class="grid grid-cols-2 gap-4"><FormField v-model="supForm.name" :label="$t('common.name')" required /><FormField v-model="supForm.code" :label="$t('procurementPage.code')" /></div>
        <div class="grid grid-cols-2 gap-4"><FormField v-model="supForm.email" :label="$t('common.email')" type="email" /><FormField v-model="supForm.phone" :label="$t('common.phone')" /></div>
        <FormField v-model="supForm.address" :label="$t('procurementPage.address')" />
      </form>
      <template #footer><div class="flex justify-end gap-2"><button class="btn btn-ghost" @click="supModal = false">{{ $t('common.cancel') }}</button><button form="sup-form" type="submit" class="btn btn-primary" :disabled="supBusy"><Spinner v-if="supBusy" :size="18" /><span v-else>{{ $t('common.create') }}</span></button></div></template>
    </Modal>

    <!-- PO modal -->
    <Modal v-model="poModal" :title="$t('procurementPage.newPurchaseOrder')" size="lg">
      <form id="po-form" class="grid gap-4" @submit.prevent="createPO">
        <div class="grid gap-4 sm:grid-cols-3">
          <div><label class="label">{{ $t('procurementPage.supplier') }}</label><select v-model="poForm.supplier_id" class="input" required><option v-for="s in suppliers" :key="s.id" :value="s.id">{{ s.name }}</option></select></div>
          <div><label class="label">{{ $t('procurementPage.warehouse') }}</label><select v-model="poForm.warehouse_id" class="input" required><option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option></select></div>
          <FormField v-model="poForm.expected_date" :label="$t('procurementPage.expectedDate')" type="date" />
        </div>
        <div>
          <div class="mb-2 flex items-center justify-between"><label class="label mb-0">{{ $t('procurementPage.lines') }}</label><button type="button" class="btn btn-ghost btn-sm" @click="addLine"><Plus class="h-4 w-4" /> {{ $t('procurementPage.addLine') }}</button></div>
          <div v-for="(l, i) in poLines" :key="i" class="mb-2 grid grid-cols-[1fr_80px_100px_auto] items-end gap-2">
            <select v-model="l.variant_id" class="input"><option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option></select>
            <input v-model.number="l.quantity_ordered" type="number" min="1" class="input" :placeholder="$t('procurementPage.qty')" />
            <input v-model.number="l.unit_cost" type="number" step="0.01" class="input" :placeholder="$t('procurementPage.cost')" />
            <button type="button" class="grid h-9 w-9 place-items-center rounded-lg text-secondary-500 hover:bg-lightbg" :disabled="poLines.length <= 1" @click="removeLine(i)"><Trash2 class="h-4 w-4" /></button>
          </div>
        </div>
        <FormField v-model="poForm.notes" :label="$t('procurementPage.notes')" />
      </form>
      <template #footer><div class="flex justify-end gap-2"><button class="btn btn-ghost" @click="poModal = false">{{ $t('common.cancel') }}</button><button form="po-form" type="submit" class="btn btn-primary" :disabled="poBusy"><Spinner v-if="poBusy" :size="18" /><span v-else>{{ $t('procurementPage.createPo') }}</span></button></div></template>
    </Modal>

    <!-- Serials modal -->
    <Modal v-model="serModal" :title="$t('procurementPage.registerSerials')">
      <form id="ser-form" class="grid gap-4" @submit.prevent="registerSerials">
        <div><label class="label">{{ $t('procurementPage.variant') }}</label><select v-model="serForm.variant_id" class="input" required><option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option></select></div>
        <div><label class="label">{{ $t('procurementPage.warehouse') }}</label><select v-model="serForm.warehouse_id" class="input" required><option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option></select></div>
        <div><label class="label">{{ $t('procurementPage.serialNumbersLabel') }}</label><textarea v-model="serForm.serials" rows="4" class="input" placeholder="SN-001&#10;SN-002"></textarea></div>
      </form>
      <template #footer><div class="flex justify-end gap-2"><button class="btn btn-ghost" @click="serModal = false">{{ $t('common.cancel') }}</button><button form="ser-form" type="submit" class="btn btn-primary" :disabled="serBusy"><Spinner v-if="serBusy" :size="18" /><span v-else>{{ $t('procurementPage.register') }}</span></button></div></template>
    </Modal>

    <!-- BOM modal -->
    <Modal v-model="bomModal" :title="$t('procurementPage.newBillOfMaterials')">
      <form id="bom-form" class="grid gap-4" @submit.prevent="createBom">
        <FormField v-model="bomForm.name" :label="$t('common.name')" required />
        <div><label class="label">{{ $t('procurementPage.outputVariant') }}</label><select v-model="bomForm.output_variant_id" class="input" required><option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option></select></div>
      </form>
      <template #footer><div class="flex justify-end gap-2"><button class="btn btn-ghost" @click="bomModal = false">{{ $t('common.cancel') }}</button><button form="bom-form" type="submit" class="btn btn-primary" :disabled="bomBusy"><Spinner v-if="bomBusy" :size="18" /><span v-else>{{ $t('common.create') }}</span></button></div></template>
    </Modal>

    <!-- BOM component modal -->
    <Modal v-model="compModal" :title="compBom ? t('procurementPage.addComponentTo', { name: compBom.name }) : t('procurementPage.addComponent')">
      <form id="comp-form" class="grid gap-4" @submit.prevent="addComponent">
        <div><label class="label">{{ $t('procurementPage.componentVariant') }}</label><select v-model="compForm.component_variant_id" class="input" required><option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option></select></div>
        <FormField v-model.number="compForm.quantity" :label="$t('common.quantity')" type="number" />
      </form>
      <template #footer><div class="flex justify-end gap-2"><button class="btn btn-ghost" @click="compModal = false">{{ $t('common.cancel') }}</button><button form="comp-form" type="submit" class="btn btn-primary" :disabled="compBusy"><Spinner v-if="compBusy" :size="18" /><span v-else>{{ $t('common.add') }}</span></button></div></template>
    </Modal>

    <!-- Work order modal -->
    <Modal v-model="woModal" :title="$t('procurementPage.newWorkOrder')">
      <form id="wo-form" class="grid gap-4" @submit.prevent="createWo">
        <div><label class="label">{{ $t('procurementPage.bom') }}</label><select v-model="woForm.bom_id" class="input" required><option v-for="b in boms" :key="b.id" :value="b.id">{{ b.name }}</option></select></div>
        <div><label class="label">{{ $t('procurementPage.warehouse') }}</label><select v-model="woForm.warehouse_id" class="input" required><option v-for="w in warehouses" :key="w.id" :value="w.id">{{ w.name }}</option></select></div>
        <FormField v-model.number="woForm.quantity" :label="$t('common.quantity')" type="number" />
      </form>
      <template #footer><div class="flex justify-end gap-2"><button class="btn btn-ghost" @click="woModal = false">{{ $t('common.cancel') }}</button><button form="wo-form" type="submit" class="btn btn-primary" :disabled="woBusy"><Spinner v-if="woBusy" :size="18" /><span v-else>{{ $t('common.create') }}</span></button></div></template>
    </Modal>
  </div>
</template>
