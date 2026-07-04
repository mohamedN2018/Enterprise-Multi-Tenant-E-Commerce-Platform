<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Search, Pencil, Trash2, Package, Download, Sparkles, Key, Image as ImageIcon, Upload } from 'lucide-vue-next';
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
import { t } from '@/i18n';
import { useValidation, required, positive } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const term = ref('');
const statusFilter = ref('');
const categories = ref([]);
const brands = ref([]);
const selected = ref([]);

const columns = computed(() => [
  { key: 'name', label: t('prod.product'), sortable: true },
  { key: 'product_type', label: t('common.type'), sortable: true },
  { key: 'variants', label: t('prod.variants'), align: 'right' },
  { key: 'price', label: t('common.price'), align: 'right' },
  { key: 'status', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.products(params)
);

const params = () => {
  const p = {};
  if (term.value.trim()) p.search = term.value.trim();
  if (statusFilter.value) p.status = statusFilter.value;
  return p;
};
const fetch = () => {
  selected.value = [];
  return load(params());
};
const changePage = (n) => {
  page.value = n;
  fetch();
};
const applyFilters = () => {
  page.value = 1;
  fetch();
};

// Bulk delete
const bulkConfirm = ref(false);
const bulkDeleting = ref(false);
const bulkDelete = async () => {
  bulkDeleting.value = true;
  try {
    await Promise.all(selected.value.map((id) => seller.deleteProduct(id)));
    ui.success(t('prod.productsDeleted', { n: selected.value.length }));
    selected.value = [];
    bulkConfirm.value = false;
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    bulkDeleting.value = false;
  }
};

const exportCsv = () => {
  const rows = items.value.map((p) => ({
    name: p.name,
    slug: p.slug,
    type: p.product_type,
    status: p.status,
    variants: p.variants?.length || 0,
    price: priceRange(p),
    currency: tenant.currency
  }));
  downloadCsv(`products-${new Date().toISOString().slice(0, 10)}.csv`, rows);
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
const blank = () => ({ name: '', name_en: '', description: '', description_en: '', product_type: 'physical', status: 'draft', category: '', brand: '' });
const form = ref(blank());
const { errors: pErrors, run: runProduct, clear: clearProduct } = useValidation(() => form.value, { name: [required()] });

const openCreate = () => {
  editing.value = null;
  form.value = blank();
  resetImage();
  showModal.value = true;
};
const openEdit = (p) => {
  editing.value = p;
  form.value = {
    name: p.name,
    name_en: p.name_en || '',
    description: p.description || '',
    description_en: p.description_en || '',
    product_type: p.product_type,
    status: p.status,
    category: p.category || '',
    brand: p.brand || ''
  };
  resetImage(p.image || '');
  showModal.value = true;
};

// Product image picker (uploaded via a separate multipart call after save).
const imageFile = ref(null);
const imagePreview = ref('');
const resetImage = (existing = '') => {
  imageFile.value = null;
  imagePreview.value = existing || '';
};
const onPickImage = (e) => {
  const f = e.target.files?.[0];
  if (!f) return;
  imageFile.value = f;
  imagePreview.value = URL.createObjectURL(f);
};

const save = async () => {
  if (!runProduct()) return;
  saving.value = true;
  try {
    const payload = { ...form.value };
    delete payload.image;
    if (!payload.category) delete payload.category;
    if (!payload.brand) delete payload.brand;
    let productId = editing.value?.id;
    if (editing.value) {
      await seller.updateProduct(productId, payload);
    } else {
      const res = await seller.createProduct(payload);
      productId = res.data?.id;
    }
    if (imageFile.value && productId) {
      await seller.uploadProductImage(productId, imageFile.value);
    }
    ui.success(editing.value ? t('prod.productUpdated') : t('prod.productCreated'));
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
const { errors: vErrors, run: runVariant, clear: clearVariant } = useValidation(() => variantForm.value, { sku: [required()], price: [positive()] });
const addingVariant = ref(false);
const addVariant = async () => {
  if (!editing.value || !runVariant()) return;
  addingVariant.value = true;
  try {
    const payload = { ...variantForm.value };
    if (!payload.compare_at_price) delete payload.compare_at_price;
    const res = await seller.createVariant(editing.value.id, payload);
    editing.value.variants = [...(editing.value.variants || []), res.data];
    variantForm.value = { name: '', sku: '', price: '', compare_at_price: '', stock_quantity: 0, is_default: false };
    ui.success(t('prod.variantAdded'));
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    addingVariant.value = false;
  }
};

// --- Generate variants (configurable products) ----------------------------
const genModal = ref(false);
const genBusy = ref(false);
const genForm = ref({ base_price: 0, sku_prefix: '' });
const generateVariants = async () => {
  genBusy.value = true;
  try {
    const payload = { base_price: genForm.value.base_price };
    if (genForm.value.sku_prefix) payload.sku_prefix = genForm.value.sku_prefix;
    await seller.generateVariants(editing.value.id, payload);
    ui.success(t('prod.variantsGenerated'));
    genModal.value = false;
    const res = await seller.product(editing.value.id);
    editing.value.variants = res.data.variants || editing.value.variants;
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    genBusy.value = false;
  }
};

// --- License keys (digital products) --------------------------------------
const keysModal = ref(false);
const keysBusy = ref(false);
const keysVariant = ref(null);
const keysText = ref('');
const openKeys = (v) => {
  keysVariant.value = v;
  keysText.value = '';
  keysModal.value = true;
};
const addKeys = async () => {
  keysBusy.value = true;
  try {
    await seller.addLicenseKeys(keysVariant.value.id, {
      keys: keysText.value.split(/[\n,]/).map((k) => k.trim()).filter(Boolean)
    });
    ui.success(t('prod.keysAdded'));
    keysModal.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    keysBusy.value = false;
  }
};

// --- Delete ---------------------------------------------------------------
const confirmDelete = ref(null);
const deleting = ref(false);
const doDelete = async () => {
  deleting.value = true;
  try {
    await seller.deleteProduct(confirmDelete.value.id);
    ui.success(t('prod.productDeleted'));
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
    const [cat, br] = await Promise.all([seller.categories({ page_size: 100 }), seller.brands({ page_size: 100 })]);
    categories.value = cat.data?.results || cat.data || [];
    brands.value = br.data?.results || br.data || [];
  } catch {
    categories.value = [];
    brands.value = [];
  }
  fetch();
});
</script>

<template>
  <div>
    <PageHeader :title="$t('prod.title')" :subtitle="$t('prod.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button class="btn btn-outline btn-sm" :disabled="!items.length" @click="exportCsv"><Download class="h-4 w-4" /> {{ $t('common.export') }}</button>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" :disabled="!tenant.hasStores" @click="openCreate">
          <Plus class="h-4 w-4" /> {{ $t('prod.addProduct') }}
        </button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <form class="relative max-w-xs flex-1" @submit.prevent="applyFilters">
        <Search class="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="term" type="search" :placeholder="$t('prod.searchProducts')" class="input ps-9" @search="applyFilters" />
      </form>
      <select v-model="statusFilter" class="input max-w-[160px]" @change="applyFilters">
        <option value="">{{ $t('common.allStatuses') }}</option>
        <option value="draft">{{ $t('status.draft') }}</option>
        <option value="published">{{ $t('status.published') }}</option>
        <option value="archived">{{ $t('status.archived') }}</option>
      </select>
    </div>

    <div v-if="selected.length" class="mb-3 flex items-center justify-between rounded-lg border border-primary-200 bg-primary-50 px-4 py-2.5">
      <span class="text-sm font-medium text-primary-700">{{ selected.length }} {{ $t('common.selected') }}</span>
      <div class="flex gap-2">
        <button class="btn btn-ghost btn-sm" @click="selected = []">{{ $t('common.clear') }}</button>
        <button v-if="tenant.canWrite" class="btn btn-danger btn-sm" @click="bulkConfirm = true"><Trash2 class="h-4 w-4" /> {{ $t('common.deleteSelected') }}</button>
      </div>
    </div>

    <DataTable :columns="columns" :rows="items" :loading="loading" :selectable="tenant.canWrite" :selected="selected" :empty-title="$t('prod.noProducts')" :empty-message="$t('prod.noProductsMsg')" @update:selected="selected = $event">
      <template #cell-name="{ row }">
        <div class="flex items-center gap-3">
          <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-400"><Package class="h-4 w-4" /></span>
          <div>
            <p class="font-medium text-ink">{{ row.name }}</p>
            <p class="text-xs text-slate-400">{{ row.slug }}</p>
          </div>
        </div>
      </template>
      <template #cell-product_type="{ value }"><span>{{ value === 'digital' ? $t('common.digital') : $t('common.physical') }}</span></template>
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
    <Modal v-model="showModal" :title="editing ? $t('prod.editProduct') : $t('prod.newProduct')" size="lg">
      <form id="product-form" class="grid gap-4" novalidate @submit.prevent="save">
        <!-- Product image -->
        <div>
          <label class="label">{{ $t('prod.image') }}</label>
          <div class="flex items-center gap-4">
            <div class="grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-lg border border-slate-200 bg-lightbg dark:border-slate-700">
              <img v-if="imagePreview" :src="imagePreview" alt="" class="h-full w-full object-cover" />
              <ImageIcon v-else class="h-6 w-6 text-slate-400" />
            </div>
            <label class="btn btn-outline btn-sm cursor-pointer">
              <Upload class="h-4 w-4" /> {{ $t('prod.chooseImage') }}
              <input type="file" accept="image/*" class="hidden" @change="onPickImage" />
            </label>
            <p class="text-xs text-muted">{{ $t('prod.imageHint') }}</p>
          </div>
        </div>
        <FormField v-model="form.name" :label="$t('common.nameAr')" :error="pErrors.name" @update:model-value="clearProduct('name')" />
        <FormField v-model="form.name_en" :label="$t('common.nameEn')" :hint="$t('common.nameEnHint')" />
        <div>
          <label class="label">{{ $t('common.description') }}</label>
          <textarea v-model="form.description" rows="3" class="input"></textarea>
        </div>
        <div>
          <label class="label">{{ $t('prod.descEn') }}</label>
          <textarea v-model="form.description_en" rows="3" class="input"></textarea>
        </div>
        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label class="label">{{ $t('common.type') }}</label>
            <select v-model="form.product_type" class="input">
              <option value="physical">{{ $t('common.physical') }}</option>
              <option value="digital">{{ $t('common.digital') }}</option>
            </select>
          </div>
          <div>
            <label class="label">{{ $t('common.status') }}</label>
            <select v-model="form.status" class="input">
              <option value="draft">{{ $t('status.draft') }}</option>
              <option value="published">{{ $t('status.published') }}</option>
              <option value="archived">{{ $t('status.archived') }}</option>
            </select>
          </div>
          <div>
            <label class="label">{{ $t('common.category') }}</label>
            <select v-model="form.category" class="input">
              <option value="">{{ $t('common.none') }}</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="label">{{ $t('common.brand') }}</label>
            <select v-model="form.brand" class="input">
              <option value="">{{ $t('common.none') }}</option>
              <option v-for="b in brands" :key="b.id" :value="b.id">{{ b.name }}</option>
            </select>
          </div>
        </div>
      </form>

      <!-- Variants (edit only) -->
      <div v-if="editing" class="mt-6 border-t border-slate-100 pt-5">
        <div class="mb-3 flex items-center justify-between">
          <h4 class="text-sm font-semibold">{{ $t('prod.variantsHeading') }}</h4>
          <button type="button" class="btn btn-ghost btn-sm" @click="genModal = true"><Sparkles class="h-4 w-4" /> {{ $t('prod.generate') }}</button>
        </div>
        <ul v-if="editing.variants?.length" class="mb-4 space-y-2">
          <li v-for="v in editing.variants" :key="v.id" class="flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <span>{{ v.name || v.sku }} <span class="text-slate-400">· {{ v.sku }}</span></span>
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ v.price }} {{ tenant.currency }}</span>
              <button v-if="editing.product_type === 'digital'" type="button" class="btn btn-ghost btn-sm" @click="openKeys(v)"><Key class="h-3.5 w-3.5" /> {{ $t('prod.keys') }}</button>
            </div>
          </li>
        </ul>
        <form class="grid grid-cols-2 gap-3 sm:grid-cols-4" novalidate @submit.prevent="addVariant">
          <FormField v-model="variantForm.name" :label="$t('common.name')" :placeholder="$t('prod.defaultVariant')" class="col-span-2 sm:col-span-1" />
          <FormField v-model="variantForm.sku" :label="$t('common.sku')" :error="vErrors.sku" @update:model-value="clearVariant('sku')" />
          <FormField v-model="variantForm.price" :label="$t('common.price')" type="number" step="0.01" :error="vErrors.price" @update:model-value="clearVariant('price')" />
          <FormField v-model.number="variantForm.stock_quantity" :label="$t('common.stock')" type="number" />
          <div class="col-span-2 sm:col-span-4">
            <button type="submit" class="btn btn-outline btn-sm" :disabled="addingVariant">
              <Plus class="h-4 w-4" /> {{ $t('prod.addVariant') }}
            </button>
          </div>
        </form>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showModal = false">{{ $t('common.close') }}</button>
          <button form="product-form" type="submit" class="btn btn-primary" :disabled="saving">
            <Spinner v-if="saving" :size="18" /><span v-else>{{ editing ? $t('common.saveChanges') : $t('prod.createProduct') }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <!-- Delete confirm -->
    <Modal :model-value="!!confirmDelete" :title="$t('prod.deleteProduct')" size="sm" @update:model-value="confirmDelete = null">
      <p class="text-sm text-slate-600">{{ $t('prod.deleteProductConfirm', { name: confirmDelete?.name }) }}</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="confirmDelete = null">{{ $t('common.cancel') }}</button>
          <button class="btn btn-danger" :disabled="deleting" @click="doDelete">
            <Spinner v-if="deleting" :size="18" /><span v-else>{{ $t('common.delete') }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <!-- Generate variants -->
    <Modal v-model="genModal" :title="$t('prod.generateVariants')" size="sm">
      <p class="mb-3 text-sm text-muted">{{ $t('prod.generateHint') }}</p>
      <div class="grid gap-4">
        <FormField v-model.number="genForm.base_price" :label="$t('prod.basePrice')" type="number" step="0.01" required />
        <FormField v-model="genForm.sku_prefix" :label="$t('prod.skuPrefix')" placeholder="e.g. TSHIRT" />
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="genModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" :disabled="genBusy" @click="generateVariants"><Spinner v-if="genBusy" :size="18" /><span v-else>{{ $t('prod.generate') }}</span></button>
        </div>
      </template>
    </Modal>

    <!-- License keys -->
    <Modal v-model="keysModal" :title="`${$t('prod.licenseKeys')}${keysVariant ? ` · ${keysVariant.sku}` : ''}`">
      <p class="mb-3 text-sm text-muted">{{ $t('prod.licenseKeysHint') }}</p>
      <textarea v-model="keysText" rows="5" class="input" placeholder="KEY-001&#10;KEY-002"></textarea>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="keysModal = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-primary" :disabled="keysBusy || !keysText.trim()" @click="addKeys"><Spinner v-if="keysBusy" :size="18" /><span v-else>{{ $t('prod.addKeys') }}</span></button>
        </div>
      </template>
    </Modal>

    <!-- Bulk delete -->
    <Modal v-model="bulkConfirm" :title="$t('prod.deleteProducts')" size="sm">
      <p class="text-sm text-slate-600">{{ $t('prod.bulkDeleteConfirm', { n: selected.length }) }}</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="bulkConfirm = false">{{ $t('common.cancel') }}</button>
          <button class="btn btn-danger" :disabled="bulkDeleting" @click="bulkDelete"><Spinner v-if="bulkDeleting" :size="18" /><span v-else>{{ $t('common.delete') }} {{ selected.length }}</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
