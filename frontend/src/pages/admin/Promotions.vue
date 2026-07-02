<script setup>
import { ref, onMounted } from 'vue';
import { Plus, Pencil, Trash2, Ticket, Download } from 'lucide-vue-next';
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
import { downloadCsv } from '@/utils/csv';

const tenant = useTenantStore();
const ui = useUiStore();

const columns = [
  { key: 'code', label: 'Code', sortable: true },
  { key: 'discount', label: 'Discount' },
  { key: 'used_count', label: 'Used', align: 'right', sortable: true },
  { key: 'window', label: 'Window' },
  { key: 'is_active', label: 'Status', sortable: true },
  { key: 'actions', label: '', align: 'right' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.coupons(params)
);
const changePage = (n) => {
  page.value = n;
  load();
};

const discountLabel = (c) =>
  c.discount_type === 'percentage' ? `${c.value}%` : `${c.value} ${tenant.currency}`;

const exportCsv = () => {
  const rows = items.value.map((c) => ({
    code: c.code,
    discount_type: c.discount_type,
    value: c.value,
    min_spend: c.min_spend ?? '',
    used_count: c.used_count,
    starts_at: (c.starts_at || '').slice(0, 10),
    ends_at: (c.ends_at || '').slice(0, 10),
    active: c.is_active
  }));
  downloadCsv(`coupons-${new Date().toISOString().slice(0, 10)}.csv`, rows);
};

const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const blank = () => ({
  code: '',
  description: '',
  discount_type: 'percentage',
  value: 10,
  min_spend: '',
  max_discount: '',
  usage_limit: '',
  per_user_limit: '',
  is_active: true
});
const form = ref(blank());

const openCreate = () => {
  editing.value = null;
  form.value = blank();
  showModal.value = true;
};
const openEdit = (c) => {
  editing.value = c;
  form.value = {
    code: c.code,
    description: c.description || '',
    discount_type: c.discount_type,
    value: c.value,
    min_spend: c.min_spend ?? '',
    max_discount: c.max_discount ?? '',
    usage_limit: c.usage_limit ?? '',
    per_user_limit: c.per_user_limit ?? '',
    is_active: c.is_active
  };
  showModal.value = true;
};

const clean = (payload) => {
  const out = { ...payload };
  ['min_spend', 'max_discount', 'usage_limit', 'per_user_limit'].forEach((k) => {
    if (out[k] === '' || out[k] == null) delete out[k];
  });
  return out;
};

const save = async () => {
  saving.value = true;
  try {
    const payload = clean(form.value);
    if (editing.value) {
      await seller.updateCoupon(editing.value.id, payload);
      ui.success('Coupon updated.');
    } else {
      await seller.createCoupon(payload);
      ui.success('Coupon created.');
    }
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
    await seller.deleteCoupon(confirmDelete.value.id);
    ui.success('Coupon deleted.');
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
    <PageHeader title="Promotions" subtitle="Create coupons to drive sales.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="exportCsv"><Download class="h-4 w-4" /> Export</button>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" :disabled="!tenant.hasStores" @click="openCreate">
          <Plus class="h-4 w-4" /> New coupon
        </button>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :rows="items" :loading="loading" empty-title="No coupons yet" empty-message="Offer discounts to attract and retain customers.">
      <template #cell-code="{ row }">
        <div class="flex items-center gap-2">
          <span class="grid h-8 w-8 place-items-center rounded-lg bg-primary-50 text-primary-600"><Ticket class="h-4 w-4" /></span>
          <span class="font-mono font-semibold text-ink">{{ row.code }}</span>
        </div>
      </template>
      <template #cell-discount="{ row }">{{ discountLabel(row) }}</template>
      <template #cell-window="{ row }">
        <span class="text-xs text-slate-500">
          {{ row.starts_at ? row.starts_at.slice(0, 10) : 'now' }} → {{ row.ends_at ? row.ends_at.slice(0, 10) : '∞' }}
        </span>
      </template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
      <template #cell-actions="{ row }">
        <div v-if="tenant.canWrite" class="flex justify-end gap-1">
          <button class="btn btn-ghost btn-sm" @click="openEdit(row)"><Pencil class="h-4 w-4" /></button>
          <button class="btn btn-ghost btn-sm text-rose-600" @click="confirmDelete = row"><Trash2 class="h-4 w-4" /></button>
        </div>
        <span v-else class="text-xs text-muted">—</span>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6">
      <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
    </div>

    <Modal v-model="showModal" :title="editing ? 'Edit coupon' : 'New coupon'">
      <form id="coupon-form" class="grid gap-4" @submit.prevent="save">
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="form.code" label="Code" placeholder="SAVE10" required />
          <div>
            <label class="label">Discount type</label>
            <select v-model="form.discount_type" class="input">
              <option value="percentage">Percentage</option>
              <option value="fixed">Fixed amount</option>
            </select>
          </div>
        </div>
        <FormField v-model="form.description" label="Description" placeholder="Optional" />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model.number="form.value" label="Value" type="number" step="0.01" required />
          <FormField v-model="form.min_spend" label="Min. spend" type="number" step="0.01" placeholder="0" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="form.usage_limit" label="Total usage limit" type="number" placeholder="Unlimited" />
          <FormField v-model="form.per_user_limit" label="Per-user limit" type="number" placeholder="Unlimited" />
        </div>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="form.is_active" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
          Active
        </label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showModal = false">Cancel</button>
          <button form="coupon-form" type="submit" class="btn btn-primary" :disabled="saving">
            <Spinner v-if="saving" :size="18" /><span v-else>{{ editing ? 'Save' : 'Create' }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <Modal :model-value="!!confirmDelete" title="Delete coupon" size="sm" @update:model-value="confirmDelete = null">
      <p class="text-sm text-slate-600">Delete coupon <span class="font-mono font-semibold">{{ confirmDelete?.code }}</span>?</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="confirmDelete = null">Cancel</button>
          <button class="btn btn-danger" :disabled="deleting" @click="doDelete">
            <Spinner v-if="deleting" :size="18" /><span v-else>Delete</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
