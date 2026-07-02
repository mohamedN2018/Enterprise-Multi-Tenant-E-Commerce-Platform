<script setup>
import { ref, onMounted } from 'vue';
import { Plus, Pencil, Trash2 } from 'lucide-vue-next';
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

const columns = [
  { key: 'name', label: 'Category' },
  { key: 'position', label: 'Position', align: 'right' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '', align: 'right' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.categories(params)
);
const changePage = (n) => {
  page.value = n;
  load();
};

const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const blank = () => ({ name: '', description: '', position: 0, is_active: true });
const form = ref(blank());

const openCreate = () => {
  editing.value = null;
  form.value = blank();
  showModal.value = true;
};
const openEdit = (c) => {
  editing.value = c;
  form.value = { name: c.name, description: c.description || '', position: c.position, is_active: c.is_active };
  showModal.value = true;
};
const save = async () => {
  saving.value = true;
  try {
    if (editing.value) {
      await seller.updateCategory(editing.value.id, form.value);
      ui.success('Category updated.');
    } else {
      await seller.createCategory(form.value);
      ui.success('Category created.');
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
    await seller.deleteCategory(confirmDelete.value.id);
    ui.success('Category deleted.');
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
    <PageHeader title="Categories" subtitle="Organize your products.">
      <template #actions>
        <button class="btn btn-primary btn-sm" :disabled="!tenant.hasStores" @click="openCreate">
          <Plus class="h-4 w-4" /> Add category
        </button>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :rows="items" :loading="loading" empty-title="No categories yet" empty-message="Group products into categories for easier browsing.">
      <template #cell-name="{ row }">
        <div>
          <p class="font-medium text-ink">{{ row.name }}</p>
          <p class="clamp-1 text-xs text-slate-400">{{ row.description || '—' }}</p>
        </div>
      </template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
      <template #cell-actions="{ row }">
        <div class="flex justify-end gap-1">
          <button class="btn btn-ghost btn-sm" @click="openEdit(row)"><Pencil class="h-4 w-4" /></button>
          <button class="btn btn-ghost btn-sm text-rose-600" @click="confirmDelete = row"><Trash2 class="h-4 w-4" /></button>
        </div>
      </template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6">
      <Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" />
    </div>

    <Modal v-model="showModal" :title="editing ? 'Edit category' : 'New category'">
      <form id="category-form" class="grid gap-4" @submit.prevent="save">
        <FormField v-model="form.name" label="Name" required />
        <div>
          <label class="label">Description</label>
          <textarea v-model="form.description" rows="2" class="input"></textarea>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model.number="form.position" label="Position" type="number" />
          <label class="mt-6 flex items-center gap-2 text-sm">
            <input v-model="form.is_active" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" />
            Active
          </label>
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showModal = false">Cancel</button>
          <button form="category-form" type="submit" class="btn btn-primary" :disabled="saving">
            <Spinner v-if="saving" :size="18" /><span v-else>{{ editing ? 'Save' : 'Create' }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <Modal :model-value="!!confirmDelete" title="Delete category" size="sm" @update:model-value="confirmDelete = null">
      <p class="text-sm text-slate-600">Delete <span class="font-semibold">{{ confirmDelete?.name }}</span>?</p>
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
