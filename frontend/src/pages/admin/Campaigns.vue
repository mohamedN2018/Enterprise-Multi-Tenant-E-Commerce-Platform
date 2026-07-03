<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Pencil, Trash2, Megaphone } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import Pagination from '@/components/ui/Pagination.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { usePaginated } from '@/composables/usePaginated';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, required, positive } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const TYPES = computed(() => [
  { value: 'flash_sale', label: t('campaignsPage.flashSale') },
  { value: 'order_discount', label: t('campaignsPage.orderDiscount') },
  { value: 'buy_x_get_y', label: t('campaignsPage.buyXGetY') },
  { value: 'free_shipping', label: t('campaignsPage.freeShipping') }
]);
const typeLabel = (v) => TYPES.value.find((x) => x.value === v)?.label || v;

const columns = computed(() => [
  { key: 'name', label: t('campaignsPage.campaign'), sortable: true },
  { key: 'campaign_type', label: t('common.type'), sortable: true },
  { key: 'window', label: t('campaignsPage.window') },
  { key: 'priority', label: t('campaignsPage.priority'), align: 'right', sortable: true },
  { key: 'is_active', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

const { items, page, total, totalPages, loading, load } = usePaginated((params) => seller.campaigns(params));
const changePage = (n) => {
  page.value = n;
  load();
};

const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const blank = () => ({
  name: '',
  description: '',
  campaign_type: 'flash_sale',
  discount_type: 'percentage',
  discount_value: 10,
  buy_quantity: 1,
  get_quantity: 1,
  get_discount_percent: 100,
  priority: 0,
  stackable: false,
  is_active: true
});
const form = ref(blank());
const isDiscount = computed(() => ['flash_sale', 'order_discount'].includes(form.value.campaign_type));
const isBxgy = computed(() => form.value.campaign_type === 'buy_x_get_y');
const { errors, run, clear } = useValidation(() => form.value, () => ({
  name: [required()],
  ...(isDiscount.value ? { discount_value: [positive()] } : {}),
  ...(isBxgy.value ? { buy_quantity: [positive()], get_quantity: [positive()], get_discount_percent: [positive()] } : {})
}));

const openCreate = () => {
  editing.value = null;
  form.value = blank();
  showModal.value = true;
};
const openEdit = (c) => {
  editing.value = c;
  form.value = { ...blank(), ...c };
  showModal.value = true;
};
const save = async () => {
  if (!run()) return;
  saving.value = true;
  try {
    const p = { name: form.value.name, description: form.value.description, campaign_type: form.value.campaign_type, priority: form.value.priority, stackable: form.value.stackable, is_active: form.value.is_active };
    if (isDiscount.value) {
      p.discount_type = form.value.discount_type;
      p.discount_value = form.value.discount_value;
    }
    if (isBxgy.value) {
      p.buy_quantity = form.value.buy_quantity;
      p.get_quantity = form.value.get_quantity;
      p.get_discount_percent = form.value.get_discount_percent;
    }
    if (editing.value) await seller.updateCampaign(editing.value.id, p);
    else await seller.createCampaign(p);
    ui.success(editing.value ? t('campaignsPage.campaignUpdated') : t('campaignsPage.campaignCreated'));
    showModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    saving.value = false;
  }
};

const confirmDelete = ref(null);
const deleting = ref(false);
const doDelete = async () => {
  deleting.value = true;
  try {
    await seller.deleteCampaign(confirmDelete.value.id);
    ui.success(t('campaignsPage.campaignDeleted'));
    confirmDelete.value = null;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    deleting.value = false;
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
});
</script>

<template>
  <div>
    <PageHeader :title="$t('campaignsPage.title')" :subtitle="$t('campaignsPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="openCreate"><Plus class="h-4 w-4" /> {{ $t('campaignsPage.newCampaign') }}</button>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :rows="items" :loading="loading" :empty-title="$t('campaignsPage.noCampaigns')" :empty-message="$t('campaignsPage.noCampaignsMsg')">
      <template #cell-name="{ row }"><div class="flex items-center gap-2"><span class="grid h-8 w-8 place-items-center rounded-lg bg-primary-50 text-primary-600"><Megaphone class="h-4 w-4" /></span><span class="font-medium text-ink">{{ row.name }}</span></div></template>
      <template #cell-campaign_type="{ value }">{{ typeLabel(value) }}</template>
      <template #cell-window="{ row }"><span class="text-xs text-muted">{{ row.starts_at ? row.starts_at.slice(0, 10) : $t('campaignsPage.now') }} → {{ row.ends_at ? row.ends_at.slice(0, 10) : '∞' }}</span></template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite" class="flex justify-end gap-1">
          <button class="btn btn-ghost btn-sm" @click="openEdit(row)"><Pencil class="h-4 w-4" /></button>
          <button class="btn btn-ghost btn-sm text-secondary-500" @click="confirmDelete = row"><Trash2 class="h-4 w-4" /></button>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>

    <Modal v-model="showModal" :title="editing ? $t('campaignsPage.editCampaign') : $t('campaignsPage.newCampaign')">
      <form id="camp-form" class="grid gap-4" novalidate @submit.prevent="save">
        <FormField v-model="form.name" :label="$t('common.name')" required :error="errors.name" @update:model-value="clear('name')" />
        <div>
          <label class="label">{{ $t('common.type') }}</label>
          <select v-model="form.campaign_type" class="input"><option v-for="t in TYPES" :key="t.value" :value="t.value">{{ t.label }}</option></select>
        </div>
        <div v-if="isDiscount" class="grid grid-cols-2 gap-4">
          <div>
            <label class="label">{{ $t('campaignsPage.discountType') }}</label>
            <select v-model="form.discount_type" class="input"><option value="percentage">{{ $t('campaignsPage.percentage') }}</option><option value="fixed">{{ $t('campaignsPage.fixed') }}</option></select>
          </div>
          <FormField v-model.number="form.discount_value" :label="$t('campaignsPage.discountValue')" type="number" step="0.01" :error="errors.discount_value" @update:model-value="clear('discount_value')" />
        </div>
        <div v-if="isBxgy" class="grid grid-cols-3 gap-4">
          <FormField v-model.number="form.buy_quantity" :label="$t('campaignsPage.buyQty')" type="number" :error="errors.buy_quantity" @update:model-value="clear('buy_quantity')" />
          <FormField v-model.number="form.get_quantity" :label="$t('campaignsPage.getQty')" type="number" :error="errors.get_quantity" @update:model-value="clear('get_quantity')" />
          <FormField v-model.number="form.get_discount_percent" :label="$t('campaignsPage.getPercentOff')" type="number" :error="errors.get_discount_percent" @update:model-value="clear('get_discount_percent')" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model.number="form.priority" :label="$t('campaignsPage.priority')" type="number" />
          <label class="mt-6 flex items-center gap-2 text-sm"><input v-model="form.stackable" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('campaignsPage.stackable') }}</label>
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="form.is_active" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('common.active') }}</label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showModal = false">{{ $t('common.cancel') }}</button>
          <button form="camp-form" type="submit" class="btn btn-primary" :disabled="saving"><Spinner v-if="saving" :size="18" /><span v-else>{{ editing ? $t('common.save') : $t('common.create') }}</span></button>
        </div>
      </template>
    </Modal>

    <Modal :model-value="!!confirmDelete" :title="$t('campaignsPage.deleteCampaign')" size="sm" @update:model-value="confirmDelete = null">
      <p class="text-sm text-slate-600">{{ $t('campaignsPage.deleteCampaignConfirm', { name: confirmDelete?.name }) }}</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="confirmDelete = null">{{ $t('common.cancel') }}</button>
          <button class="btn btn-danger" :disabled="deleting" @click="doDelete"><Spinner v-if="deleting" :size="18" /><span v-else>{{ $t('common.delete') }}</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
