<script setup>
import { ref, onMounted } from 'vue';
import { Plus, Gift } from 'lucide-vue-next';
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
  { key: 'code', label: 'Code', sortable: true },
  { key: 'initial_balance', label: 'Initial', align: 'right', sortable: true },
  { key: 'balance', label: 'Balance', align: 'right', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'created_at', label: 'Issued' }
];

const { items, page, total, totalPages, loading, load } = usePaginated((params) => seller.giftCards(params));
const changePage = (n) => {
  page.value = n;
  load();
};

const modal = ref(false);
const busy = ref(false);
const form = ref({ amount: 0, code: '' });
const issue = async () => {
  busy.value = true;
  try {
    const payload = { amount: form.value.amount };
    if (form.value.code.trim()) payload.code = form.value.code.trim();
    await seller.issueGiftCard(payload);
    ui.success('Gift card issued.');
    modal.value = false;
    form.value = { amount: 0, code: '' };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busy.value = false;
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
});
</script>

<template>
  <div>
    <PageHeader title="Gift cards" subtitle="Issue and track store gift cards.">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">Read-only</span>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="modal = true"><Plus class="h-4 w-4" /> Issue card</button>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :rows="items" :loading="loading" empty-title="No gift cards" empty-message="Issue gift cards for customers to redeem to their wallet.">
      <template #cell-code="{ row }"><div class="flex items-center gap-2"><span class="grid h-8 w-8 place-items-center rounded-lg bg-primary-50 text-primary-600"><Gift class="h-4 w-4" /></span><span class="font-mono font-semibold">{{ row.code }}</span></div></template>
      <template #cell-initial_balance="{ row }">{{ row.initial_balance }} {{ tenant.currency }}</template>
      <template #cell-balance="{ row }">{{ row.balance }} {{ tenant.currency }}</template>
      <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
    </DataTable>

    <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>

    <Modal v-model="modal" title="Issue gift card" size="sm">
      <form id="gc-form" class="grid gap-4" @submit.prevent="issue">
        <FormField v-model.number="form.amount" label="Amount" type="number" step="0.01" required />
        <FormField v-model="form.code" label="Code (optional)" placeholder="Auto-generated if blank" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="modal = false">Cancel</button>
          <button form="gc-form" type="submit" class="btn btn-primary" :disabled="busy"><Spinner v-if="busy" :size="18" /><span v-else>Issue</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
