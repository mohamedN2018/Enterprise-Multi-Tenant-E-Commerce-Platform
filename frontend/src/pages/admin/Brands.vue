<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Pencil, Trash2 } from 'lucide-vue-next';
import { t } from '@/i18n';
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

const columns = computed(() => [
  { key: 'name', label: t('common.brand'), sortable: true },
  { key: 'is_active', label: t('common.status'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

const { items, page, total, totalPages, loading, load } = usePaginated((params) => seller.brands(params));
const changePage = (n) => {
  page.value = n;
  load();
};

const showModal = ref(false);
const editing = ref(null);
const saving = ref(false);
const blank = () => ({ name: '', description: '', is_active: true });
const form = ref(blank());

const openCreate = () => {
  editing.value = null;
  form.value = blank();
  showModal.value = true;
};
const openEdit = (b) => {
  editing.value = b;
  form.value = { name: b.name, description: b.description || '', is_active: b.is_active };
  showModal.value = true;
};
const save = async () => {
  saving.value = true;
  try {
    if (editing.value) {
      await seller.updateBrand(editing.value.id, form.value);
      ui.success(t('brandsPage.brandUpdated'));
    } else {
      await seller.createBrand(form.value);
      ui.success(t('brandsPage.brandCreated'));
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
    await seller.deleteBrand(confirmDelete.value.id);
    ui.success(t('brandsPage.brandDeleted'));
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
    <PageHeader :title="$t('brandsPage.title')" :subtitle="$t('brandsPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" :disabled="!tenant.hasStores" @click="openCreate"><Plus class="h-4 w-4" /> {{ $t('brandsPage.addBrand') }}</button>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :rows="items" :loading="loading" :empty-title="$t('brandsPage.emptyTitle')" :empty-message="$t('brandsPage.emptyMessage')">
      <template #cell-name="{ row }">
        <div><p class="font-medium text-ink">{{ row.name }}</p><p class="clamp-1 text-xs text-slate-400">{{ row.description || '—' }}</p></div>
      </template>
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

    <Modal v-model="showModal" :title="editing ? $t('brandsPage.editBrand') : $t('brandsPage.newBrand')">
      <form id="brand-form" class="grid gap-4" @submit.prevent="save">
        <FormField v-model="form.name" :label="$t('common.name')" required />
        <div>
          <label class="label">{{ $t('common.description') }}</label>
          <textarea v-model="form.description" rows="2" class="input"></textarea>
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="form.is_active" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('common.active') }}</label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showModal = false">{{ $t('common.cancel') }}</button>
          <button form="brand-form" type="submit" class="btn btn-primary" :disabled="saving"><Spinner v-if="saving" :size="18" /><span v-else>{{ editing ? $t('common.save') : $t('common.create') }}</span></button>
        </div>
      </template>
    </Modal>

    <Modal :model-value="!!confirmDelete" :title="$t('brandsPage.deleteBrand')" size="sm" @update:model-value="confirmDelete = null">
      <p class="text-sm text-slate-600">{{ $t('brandsPage.deletePromptPre') }} <span class="font-semibold">{{ confirmDelete?.name }}</span>{{ $t('brandsPage.deletePromptPost') }}</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="confirmDelete = null">{{ $t('common.cancel') }}</button>
          <button class="btn btn-danger" :disabled="deleting" @click="doDelete"><Spinner v-if="deleting" :size="18" /><span v-else>{{ $t('common.delete') }}</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
