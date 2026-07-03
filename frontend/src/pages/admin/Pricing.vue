<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Users, Trash2, Tag } from 'lucide-vue-next';
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

const tenant = useTenantStore();
const ui = useUiStore();

const tab = ref('groups');
const loading = ref(true);
const groups = ref([]);
const rules = ref([]);
const variantOptions = ref([]);
const variantMap = ref({});

const groupMap = computed(() => Object.fromEntries(groups.value.map((g) => [g.id, g.name])));

const groupCols = computed(() => [
  { key: 'name', label: t('pricingPage.group'), sortable: true },
  { key: 'code', label: t('pricingPage.code') },
  { key: 'priority', label: t('pricingPage.priority'), align: 'right', sortable: true },
  { key: 'is_default', label: t('pricingPage.default') }
]);
const ruleCols = computed(() => [
  { key: 'variant', label: t('pricingPage.variant') },
  { key: 'customer_group', label: t('pricingPage.group') },
  { key: 'min_quantity', label: t('pricingPage.minQty'), align: 'right', sortable: true },
  { key: 'rule_type', label: t('common.type') },
  { key: 'value', label: t('pricingPage.value'), align: 'right', sortable: true },
  { key: 'is_active', label: t('common.status') },
  { key: 'actions', label: '', align: 'right' }
]);

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
    ui.success(t('pricingPage.groupCreated'));
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
    ui.success(t('pricingPage.ruleCreated'));
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
    ui.success(t('pricingPage.ruleDeleted'));
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
    <PageHeader :title="$t('pricingPage.title')" :subtitle="$t('pricingPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button v-if="tenant.canWrite && tab === 'groups'" class="btn btn-primary btn-sm" @click="groupModal = true"><Plus class="h-4 w-4" /> {{ $t('pricingPage.addGroup') }}</button>
        <button v-if="tenant.canWrite && tab === 'rules'" class="btn btn-primary btn-sm" :disabled="!variantOptions.length" @click="openRule"><Plus class="h-4 w-4" /> {{ $t('pricingPage.addRule') }}</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex gap-2">
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'groups' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'groups'"><Users class="me-1 inline h-4 w-4" /> {{ $t('pricingPage.customerGroups') }}</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="tab === 'rules' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="tab = 'rules'"><Tag class="me-1 inline h-4 w-4" /> {{ $t('pricingPage.priceRules') }}</button>
    </div>

    <DataTable v-if="tab === 'groups'" :columns="groupCols" :rows="groups" :loading="loading" :empty-title="$t('pricingPage.noGroups')" :empty-message="$t('pricingPage.noGroupsMsg')">
      <template #cell-name="{ row }"><span class="font-medium text-ink">{{ row.name }}</span></template>
      <template #cell-code="{ value }"><span class="text-xs text-muted">{{ value || '—' }}</span></template>
      <template #cell-is_default="{ value }"><StatusBadge v-if="value" status="active" :label="$t('pricingPage.default')" /><span v-else class="text-xs text-muted">—</span></template>
    </DataTable>

    <DataTable v-else :columns="ruleCols" :rows="rules" :loading="loading" :empty-title="$t('pricingPage.noRules')" :empty-message="$t('pricingPage.noRulesMsg')">
      <template #cell-variant="{ value }"><span class="font-medium text-ink">{{ variantMap[value] || String(value).slice(0, 8) }}</span></template>
      <template #cell-customer_group="{ value }">{{ value ? groupMap[value] || $t('pricingPage.group') : $t('pricingPage.allCustomers') }}</template>
      <template #cell-rule_type="{ value }"><span>{{ value === 'percentage' ? $t('pricingPage.percentage') : $t('pricingPage.fixed') }}</span></template>
      <template #cell-value="{ row }">{{ row.value }} {{ row.rule_type === 'percentage' ? '%' : tenant.currency }}</template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
      <template #cell-actions="{ row }">
        <button v-if="tenant.canWrite" class="btn btn-ghost btn-sm text-secondary-500" @click="deleteRule(row)"><Trash2 class="h-4 w-4" /></button>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <!-- Group modal -->
    <Modal v-model="groupModal" :title="$t('pricingPage.newGroup')">
      <form id="group-form" class="grid gap-4" @submit.prevent="createGroup">
        <FormField v-model="groupForm.name" :label="$t('common.name')" placeholder="VIP" required />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="groupForm.code" :label="$t('pricingPage.code')" placeholder="VIP" />
          <FormField v-model.number="groupForm.priority" :label="$t('pricingPage.priority')" type="number" />
        </div>
        <FormField v-model="groupForm.description" :label="$t('common.description')" />
        <label class="flex items-center gap-2 text-sm"><input v-model="groupForm.is_default" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('pricingPage.defaultGroup') }}</label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="groupModal = false">{{ $t('common.cancel') }}</button>
          <button form="group-form" type="submit" class="btn btn-primary" :disabled="groupBusy"><Spinner v-if="groupBusy" :size="18" /><span v-else>{{ $t('common.create') }}</span></button>
        </div>
      </template>
    </Modal>

    <!-- Rule modal -->
    <Modal v-model="ruleModal" :title="$t('pricingPage.newRule')">
      <form id="rule-form" class="grid gap-4" @submit.prevent="createRule">
        <div>
          <label class="label">{{ $t('pricingPage.variant') }}</label>
          <select v-model="ruleForm.variant_id" class="input" required>
            <option v-for="v in variantOptions" :key="v.id" :value="v.id">{{ v.label }}</option>
          </select>
        </div>
        <div>
          <label class="label">{{ $t('pricingPage.customerGroup') }}</label>
          <select v-model="ruleForm.customer_group_id" class="input">
            <option value="">{{ $t('pricingPage.allCustomers') }}</option>
            <option v-for="g in groups" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <FormField v-model.number="ruleForm.min_quantity" :label="$t('pricingPage.minQty')" type="number" />
          <div>
            <label class="label">{{ $t('common.type') }}</label>
            <select v-model="ruleForm.rule_type" class="input">
              <option value="fixed">{{ $t('pricingPage.fixed') }}</option>
              <option value="percentage">{{ $t('pricingPage.percentage') }}</option>
            </select>
          </div>
          <FormField v-model.number="ruleForm.value" :label="$t('pricingPage.value')" type="number" step="0.01" required />
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="ruleModal = false">{{ $t('common.cancel') }}</button>
          <button form="rule-form" type="submit" class="btn btn-primary" :disabled="ruleBusy"><Spinner v-if="ruleBusy" :size="18" /><span v-else>{{ $t('common.create') }}</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
