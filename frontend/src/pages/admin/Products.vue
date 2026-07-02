<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Search, Pencil, Trash2, Package } from 'lucide-vue-next';
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

const tenant = useTenantStore();
const ui = useUiStore();

const term = ref('');
const statusFilter = ref('');
const categories = ref([]);

const columns = [
  { key: 'name', label: 'Product' },
  { key: 'product_type', label: 'Type' },
  { key: 'variants', label: 'Variants', align: 'right' },
  { key: 'price', label: 'Price', align: 'right' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '', align: 'right' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.products(params)
);

const params = () => {
  const p = {};
  if (term.value.trim()) p.search = term.value.trim();
  if (statusFilter.value) p.status = statusFilter.value;
  return p;
};
const fetch = () => load(params());
const changePage = (n) => {
  page.value = n;
  fetch();
};
const applyFilters = () => {
  page.value = 1;
  fetch();
};

const priceRange = (p) => {
  const prices = (p.variants || []).map((v) => Number(v.price)).filter((n) => !Number.isNaN(n));
  if (!prices.length) return '—';
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  return min === max ? `${min}` : `${min}–${max}`;
};

// --- Create / edit ---------------------------------------------------------
const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const blank = () => ({ name: '', description: '', product_type: 'physical', status: 'draft', category: '' });
const form = ref(blank());

const openCreate = () => {
  editing.value = null;
  form.value = blank();
  showModal.value = true;
};
const openEdit = (p) => {
  editing.value = p;
  form.value = {
    name: p.name,
    description: p.description || '',
    product_type: p.product_type,
    status: p.status,
    category: p.category || ''
  };
  showModal.value = true;
};

const save = async () => {
  saving.value = true;
  try {
    const payload = { ...form.value };
    if (!payload.category) delete payload.category;
    if (editing.value) {
      await seller.updateProduct(editing.value.id, payload);
      ui.success('Product updated.');
    } else {
      await seller.createProduct(payload);
      ui.success('Product created.');
    }
    showModal.value = false;
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    saving.value = false;
  }
};

// --- Variant quick-add (within edit) --------------------------------------
const variantForm = ref({ name: '', sku: '', price: '', compare_at_price: '', stock_quantity: 0, is_default: false });
const addingVariant = ref(false);
const addVariant = async () => {
  if (!editing.value) return;
  addingVariant.value = true;
  try {
    const payload = { ...variantForm.value };
    if (!payload.compare_at_price) delete payload.compare_at_price;
    const res = await seller.createVariant(editing.value.id, payload);
    editing.value.variants = [...(editing.value.variants || []), res.data];
    variantForm.value = { name: '', sku: '', price: '', compare_at_price: '', stock_quantity: 0, is_default: false };
    ui.success('Variant added.');
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    addingVariant.value = false;
  }
};

// --- Delete ---------------------------------------------------------------
const confirmDelete = ref(null);
const deleting = ref(false);
const doDelete = async () => {
  deleting.value = true;
  try {
    await seller.deleteProduct(confirmDelete.value.id);
    ui.success('Product deleted.');
    confirmDelete.value = null;
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    deleting.value = false;
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (!id) return;
  try {
    const cat = await seller.categories();
    categories.value = cat.data?.results || cat.data || [];
  } catch {
    categories.value = [];
  }
  fetch();
});
</script>

<template>
  <div>
    <PageHeader title="Products" subtitle="Manage your catalog.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" :disabled="!tenant.hasStores" @click="openCreate">
          <Plus class="h-4 w-4" /> Add product
        </button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="relative max-w-xs flex-1" @submit.prevent="applyFilters">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="term" type="search" placeholder="Search products…" class="input pl-9" @search="applyFilters" />
      </form>
      <select v-model="statusFilter" class="input max-w-[160px]" @change="applyFilters">
        <option value="">All statuses</option>
        <option value="draft">Draft</option>
        <option value="published">Published</option>
        <option value="archived">Archived</option>
      </select>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" empty-title="No products yet" empty-message="Create your first product to start selling.">
      <template #cell-name="{ row }">
        <div class="flex items-center gap-3">
          <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-400"><Package class="h-4 w-4" /></span>
          <div>
            <p class="font-medium text-ink">{{ row.name }}</p>
            <p class="text-xs text-slate-400">{{ row.slug }}</p>
          </div>
        </div>
      </template>
      <template #cell-product_type="{ value }"><span class="capitalize">{{ value }}</span></template>
      <template #cell-variants="{ row }">{{ row.variants?.length || 0 }}</template>
      <template #cell-price="{ row }">{{ priceRange(row) }} {{ tenant.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
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

    <!-- Create / edit modal -->
    <Modal v-model="showModal" :title="editing ? 'Edit product' : 'New product'" size="lg">
      <form id="product-form" class="grid gap-4" @submit.prevent="save">
        <FormField v-model="form.name" label="Name" required />
        <div>
          <label class="label">Description</label>
          <textarea v-model="form.description" rows="3" class="input"></textarea>
        </div>
        <div class="grid gap-4 sm:grid-cols-3">
          <div>
            <label class="label">Type</label>
            <select v-model="form.product_type" class="input">
              <option value="physical">Physical</option>
              <option value="digital">Digital</option>
            </select>
          </div>
          <div>
            <label class="label">Status</label>
            <select v-model="form.status" class="input">
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div>
            <label class="label">Category</label>
            <select v-model="form.category" class="input">
              <option value="">None</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
        </div>
      </form>

      <!-- Variants (edit only) -->
      <div v-if="editing" class="mt-6 border-t border-slate-100 pt-5">
        <h4 class="mb-3 text-sm font-semibold">Variants</h4>
        <ul v-if="editing.variants?.length" class="mb-4 space-y-2">
          <li v-for="v in editing.variants" :key="v.id" class="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <span>{{ v.name || v.sku }} <span class="text-slate-400">· {{ v.sku }}</span></span>
            <span class="font-medium">{{ v.price }} {{ tenant.currency }}</span>
          </li>
        </ul>
        <form class="grid grid-cols-2 gap-3 sm:grid-cols-4" @submit.prevent="addVariant">
          <FormField v-model="variantForm.name" label="Name" placeholder="Default" class="col-span-2 sm:col-span-1" />
          <FormField v-model="variantForm.sku" label="SKU" required />
          <FormField v-model="variantForm.price" label="Price" type="number" step="0.01" required />
          <FormField v-model.number="variantForm.stock_quantity" label="Stock" type="number" />
          <div class="col-span-2 sm:col-span-4">
            <button type="submit" class="btn btn-outline btn-sm" :disabled="addingVariant">
              <Plus class="h-4 w-4" /> Add variant
            </button>
          </div>
        </form>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showModal = false">Close</button>
          <button form="product-form" type="submit" class="btn btn-primary" :disabled="saving">
            <Spinner v-if="saving" :size="18" /><span v-else>{{ editing ? 'Save changes' : 'Create product' }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <!-- Delete confirm -->
    <Modal :model-value="!!confirmDelete" title="Delete product" size="sm" @update:model-value="confirmDelete = null">
      <p class="text-sm text-slate-600">Are you sure you want to delete <span class="font-semibold">{{ confirmDelete?.name }}</span>? This cannot be undone.</p>
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
