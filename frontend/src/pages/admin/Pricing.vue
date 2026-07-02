<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Users, Trash2, Tag } from 'lucide-vue-next';
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

const tab = ref('groups');
const loading = ref(true);
const groups = ref([]);
const rules = ref([]);
const variantOptions = ref([]);
const variantMap = ref({});

const groupMap = computed(() => Object.fromEntries(groups.value.map((g) => [g.id, g.name])));

const groupCols = [
  { key: 'name', label: 'Group', sortable: true },
  { key: 'code', label: 'Code' },
  { key: 'priority', label: 'Priority', align: 'right', sortable: true },
  { key: 'is_default', label: 'Default' }
];
const ruleCols = [
  { key: 'variant', label: 'Variant' },
  { key: 'customer_group', label: 'Group' },
  { key: 'min_quantity', label: 'Min qty', align: 'right', sortable: true },
  { key: 'rule_type', label: 'Type' },
  { key: 'value', label: 'Value', align: 'right', sortable: true },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '', align: 'right' }
];

const load = async () => {
  loading.value = true;
  try {
    const [g, r, prod] = await Promise.all([
      seller.customerGroups(),
      seller.priceRules(),
      seller.products({ page_size: 100 })
    ]);
    groups.value = g.data?.results || g.data || [];
    rules.value = r.data?.results || r.data || [];
    const opts = [];
    const map = {};
    (prod.data?.results || prod.data || []).forEach((p) => {
      (p.variants || []).forEach((v) => {
        const label = `${p.name}${v.name ? ` · ${v.name}` : ''} (${v.sku})`;
        opts.push({ id: v.id, label });
        map[v.id] = label;
      });
    });
    variantOptions.value = opts;
    variantMap.value = map;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

// Group create
const groupModal = ref(false);
const groupBusy = ref(false);
const groupForm = ref({ name: '', code: '', description: '', priority: 0, is_default: false });
const createGroup = async () => {
  groupBusy.value = true;
  try {
    const payload = { ...groupForm.value };
    if (!payload.code) delete payload.code;
    await seller.createCustomerGroup(payload);
    ui.success('Group created.');
    groupModal.value = false;
    groupForm.value = { name: '', code: '', description: '', priority: 0, is_default: false };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    groupBusy.value = false;
  }
};

// Rule create
const ruleModal = ref(false);
const ruleBusy = ref(false);
const ruleForm = ref({ variant_id: '', customer_group_id: '', min_quantity: 1, rule_type: 'fixed', value: 0, is_active: true });
const openRule = () => {
  ruleForm.value = { variant_id: variantOptions.value[0]?.id || '', customer_group_id: '', min_quantity: 1, rule_type: 'fixed', value: 0, is_active: true };
  ruleModal.value = true;
};
const createRule = async () => {
  ruleBusy.value = true;
  try {
    const payload = { ...ruleForm.value };
    if (!payload.customer_group_id) delete payload.customer_group_id;
    await seller.createPriceRule(payload);
    ui.success('Price rule created.');
    ruleModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    ruleBusy.value = false;
  }
};
const deleteRule = async (r) => {
  try {
    await seller.deletePriceRule(r.id);
    rules.value = rules.value.filter((x) => x.id !== r.id);
    ui.success('Rule deleted.');
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
  else loading.value = false;
});
</script>

<template>
  <div>
    <PageHeader title="Pricing" subtitle="Customer groups and tiered price rules.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button v-if="tenant.canWrite && tab === 'groups'" class="btn btn-primary btn-sm" @click="groupModal = true"><Plus class="h-4 w-4" /> Add group</button>
        <button v-if="tenant.canWrite && tab === 'rules'" class="btn btn-primary btn-sm" :disabled="!variantOptions.length" @click="openRule"><Plus class="h-4 w-4" /> Add rule</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex gap-2">
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'groups' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'groups'"><Users class="mr-1 inline h-4 w-4" /> Customer groups</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'rules' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'rules'"><Tag class="mr-1 inline h-4 w-4" /> Price rules</button>
    </div>

    <DataTable v-if="tab === 'groups'" :columns="groupCols" :rows="groups" :loading="loading" empty-title="No customer groups" empty-message="Create groups (e.g. VIP, Wholesale) to apply special pricing.">
      <template #cell-name="{ row }"><span class="font-medium text-ink">{{ row.name }}</span></template>
      <template #cell-code="{ value }"><span class="text-xs text-muted">{{ value || '—' }}</span></template>
      <template #cell-is_default="{ value }"><StatusBadge v-if="value" status="active" label="Default" /><span v-else class="text-xs text-muted">—</span></template>
    </DataTable>

    <DataTable v-else :columns="ruleCols" :rows="rules" :loading="loading" empty-title="No price rules" empty-message="Add tiered or group-based prices for your variants.">
      <template #cell-variant="{ value }"><span class="font-medium text-ink">{{ variantMap[value] || String(value).slice(0, 8) }}</span></template>
      <template #cell-customer_group="{ value }">{{ value ? groupMap[value] || 'Group' : 'All customers' }}</template>
      <template #cell-rule_type="{ value }"><span class="capitalize">{{ value }}</span></template>
      <template #cell-value="{ row }">{{ row.value }} {{ row.rule_type === 'percentage' ? '%' : tenant.currency }}</template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
      <template #cell-actions="{ row }">
        <button v-if="tenant.canWrite" class="btn btn-ghost btn-sm text-secondary-500" @click="deleteRule(row)"><Trash2 class="h-4 w-4" /></button>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <!-- Group modal -->
    <Modal v-model="groupModal" title="New customer group">
      <form id="group-form" class="grid gap-4" @submit.prevent="createGroup">
        <FormField v-model="groupForm.name" label="Name" placeholder="VIP" required />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="groupForm.code" label="Code" placeholder="VIP" />
          <FormField v-model.number="groupForm.priority" label="Priority" type="number" />
        </div>
        <FormField v-model="groupForm.description" label="Description" />
        <label class="flex items-center gap-2 text-sm"><input v-model="groupForm.is_default" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> Default group</label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="groupModal = false">Cancel</button>
          <button form="group-form" type="submit" class="btn btn-primary" :disabled="groupBusy"><Spinner v-if="groupBusy" :size="18" /><span v-else>Create</span></button>
        </div>
      </template>
    </Modal>

    <!-- Rule modal -->
    <Modal v-model="ruleModal" title="New price rule">
      <form id="rule-form" class="grid gap-4" @submit.prevent="createRule">
        <div>
          <label class="label">Variant</label>
          <select v-model="ruleForm.variant_id" class="input" required>
            <option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option>
          </select>
        </div>
        <div>
          <label class="label">Customer group</label>
          <select v-model="ruleForm.customer_group_id" class="input">
            <option value="">All customers</option>
            <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <FormField v-model.number="ruleForm.min_quantity" label="Min qty" type="number" />
          <div>
            <label class="label">Type</label>
            <select v-model="ruleForm.rule_type" class="input">
              <option value="fixed">Fixed</option>
              <option value="percentage">Percentage</option>
            </select>
          </div>
          <FormField v-model.number="ruleForm.value" label="Value" type="number" step="0.01" required />
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="ruleModal = false">Cancel</button>
          <button form="rule-form" type="submit" class="btn btn-primary" :disabled="ruleBusy"><Spinner v-if="ruleBusy" :size="18" /><span v-else>Create</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
