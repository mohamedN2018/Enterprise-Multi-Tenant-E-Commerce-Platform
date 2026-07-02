<script setup>
import { ref, computed, onMounted } from 'vue';
import { Wallet, Percent, Banknote, ArrowDownToLine } from 'lucide-vue-next';
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

const loading = ref(true);
const account = ref(null);
const ledger = ref([]);
const payouts = ref([]);

const currency = computed(() => account.value?.currency || tenant.currency);

const ledgerColumns = [
  { key: 'created_at', label: 'Date', sortable: true },
  { key: 'entry_type', label: 'Type', sortable: true },
  { key: 'gross_amount', label: 'Gross', align: 'right' },
  { key: 'commission_amount', label: 'Commission', align: 'right' },
  { key: 'net_amount', label: 'Net', align: 'right', sortable: true },
  { key: 'balance_after', label: 'Balance', align: 'right' }
];
const payoutColumns = [
  { key: 'created_at', label: 'Requested', sortable: true },
  { key: 'amount', label: 'Amount', align: 'right', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'reference', label: 'Reference' },
  { key: 'actions', label: '', align: 'right' }
];

const load = async () => {
  loading.value = true;
  try {
    await tenant.ensureReady();
    const [acc, led, pay] = await Promise.all([
      seller.payoutAccount().catch(() => ({ data: null })),
      seller.payoutLedger({ page_size: 20 }).catch(() => ({ data: [] })),
      seller.payouts({ page_size: 20 }).catch(() => ({ data: [] }))
    ]);
    account.value = acc.data;
    ledger.value = led.data?.results || led.data || [];
    payouts.value = pay.data?.results || pay.data || [];
  } finally {
    loading.value = false;
  }
};

// Request payout
const modal = ref(false);
const busy = ref(false);
const amount = ref(0);
const openRequest = () => {
  amount.value = Number(account.value?.balance || 0);
  modal.value = true;
};
const requestPayout = async () => {
  busy.value = true;
  try {
    await seller.requestPayout({ amount: amount.value });
    ui.success('Payout requested.');
    modal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busy.value = false;
  }
};

const markPaid = async (p) => {
  try {
    await seller.markPayoutPaid(p.id);
    ui.success('Marked as paid.');
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

onMounted(load);
</script>

<template>
  <div>
    <PageHeader title="Payouts" subtitle="Your seller balance, ledger and payout requests.">
      <template #actions>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" :disabled="!Number(account?.balance)" @click="openRequest"><ArrowDownToLine class="h-4 w-4" /> Request payout</button>
      </template>
    </PageHeader>

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="28" label="Loading…" /></div>

    <template v-else>
      <!-- Summary -->
      <div class="grid gap-4 sm:grid-cols-3">
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-emerald-50 text-emerald-600"><Wallet class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ account?.balance || '0.00' }} {{ currency }}</p><p class="text-sm text-muted">Available balance</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-primary-50 text-primary-600"><Percent class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ account?.commission_rate ?? '—' }}%</p><p class="text-sm text-muted">Platform commission</p></div>
        </div>
        <div class="card flex items-center gap-4 p-5">
          <span class="grid h-12 w-12 place-items-center rounded-lg bg-sky-50 text-sky-600"><Banknote class="h-6 w-6" /></span>
          <div><p class="font-heading text-2xl font-bold">{{ payouts.length }}</p><p class="text-sm text-muted">Payout requests</p></div>
        </div>
      </div>

      <!-- Payouts -->
      <h2 class="section-title mb-4 mt-8 text-xl">Payout requests</h2>
      <DataTable :columns="payoutColumns" :rows="payouts" empty-title="No payouts yet" empty-message="Request a payout once you have a balance.">
        <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
        <template #cell-amount="{ row }">{{ row.amount }} {{ currency }}</template>
        <template #cell-status="{ value }"><StatusBadge :status="value" /></template>
        <template #cell-reference="{ value }"><span class="text-xs text-muted">{{ value || '—' }}</span></template>
        <template #cell-actions="{ row }">
          <button v-if="tenant.canDeleteStore && row.status !== 'paid'" class="btn btn-ghost btn-sm" @click="markPaid(row)">Mark paid</button>
          <span v-else class="text-xs text-muted">—</span>
        </template>
      </DataTable>

      <!-- Ledger -->
      <h2 class="section-title mb-4 mt-8 text-xl">Earnings ledger</h2>
      <DataTable :columns="ledgerColumns" :rows="ledger" empty-title="No ledger entries" empty-message="Confirmed orders will post earnings here.">
        <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
        <template #cell-entry_type="{ value }"><span class="capitalize">{{ String(value).replace(/_/g, ' ') }}</span></template>
        <template #cell-gross_amount="{ value }">{{ value }} {{ currency }}</template>
        <template #cell-commission_amount="{ value }">{{ value }} {{ currency }}</template>
        <template #cell-net_amount="{ value }">{{ value }} {{ currency }}</template>
        <template #cell-balance_after="{ value }">{{ value }} {{ currency }}</template>
      </DataTable>
    </template>

    <Modal v-model="modal" title="Request payout" size="sm">
      <p class="mb-3 text-sm text-muted">Available balance: <span class="font-semibold text-ink">{{ account?.balance || '0.00' }} {{ currency }}</span></p>
      <FormField v-model.number="amount" label="Amount" type="number" step="0.01" required />
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="modal = false">Cancel</button>
          <button class="btn btn-primary" :disabled="busy" @click="requestPayout"><Spinner v-if="busy" :size="18" /><span v-else>Request</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
