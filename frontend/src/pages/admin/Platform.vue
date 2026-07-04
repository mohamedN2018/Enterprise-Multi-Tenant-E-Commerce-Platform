<script setup>
import { ref, computed, onMounted } from 'vue';
import {
  Store as StoreIcon,
  ShieldAlert,
  ExternalLink,
  Plus,
  Users,
  Pencil,
  Eye,
  Building2,
  UserCog,
  Search,
  Inbox,
  Check,
  X
} from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import DataTable from '@/components/ui/DataTable.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { platform } from '@/services/platform';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, required, email, iso2, numberMin, positive } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const stores = ref([]);
const sellers = ref([]);
const requests = ref([]);

const STATUSES = ['draft', 'active', 'suspended', 'closed'];

const load = async () => {
  loading.value = true;
  try {
    await tenant.ensureReady();
    if (!tenant.isPlatform) return;
    const [st, sl, rq] = await Promise.all([
      platform.stores(),
      platform.sellers(),
      platform.requests({ status: 'pending' })
    ]);
    stores.value = st.data || [];
    sellers.value = sl.data || [];
    requests.value = rq.data || [];
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const requestColumns = computed(() => [
  { key: 'requester_email', label: t('platformPage.seller') },
  { key: 'target', label: t('platformPage.request') },
  { key: 'note', label: t('common.description') },
  { key: 'actions', label: '', align: 'right' }
]);

const resolvingId = ref(null);
const resolveReq = async (req, approve) => {
  resolvingId.value = req.id;
  try {
    if (approve) await platform.approveRequest(req.id);
    else await platform.rejectRequest(req.id);
    ui.success(approve ? t('platformPage.requestApproved') : t('platformPage.requestRejected'));
    await load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    resolvingId.value = null;
  }
};

const kpis = computed(() => [
  { label: t('platformPage.totalStores'), value: stores.value.length, icon: StoreIcon, tone: 'text-primary-600 bg-primary-50' },
  { label: t('platformPage.activeStores'), value: stores.value.filter((s) => s.status === 'active').length, icon: Building2, tone: 'text-emerald-600 bg-emerald-50' },
  { label: t('platformPage.sellers'), value: sellers.value.length, icon: UserCog, tone: 'text-violet-600 bg-violet-50' },
  { label: t('platformPage.employees'), value: stores.value.reduce((a, s) => a + (s.employee_count || 0), 0), icon: Users, tone: 'text-sky-600 bg-sky-50' }
]);

const storeColumns = computed(() => [
  { key: 'name', label: t('platformPage.store') },
  { key: 'owner_email', label: t('platformPage.owner') },
  { key: 'employees', label: t('platformPage.employees'), align: 'center' },
  { key: 'status', label: t('common.status') },
  { key: 'actions', label: '', align: 'right' }
]);

const sellerColumns = computed(() => [
  { key: 'email', label: t('platformPage.seller') },
  { key: 'stores', label: t('platformPage.ownedStores'), align: 'center' },
  { key: 'actions', label: '', align: 'right' }
]);

const viewStorefront = (s) => window.open(`/products?store=${s.slug}`, '_blank', 'noopener');

// --- Create a store for a contracted seller --------------------------------
const showCreate = ref(false);
const creating = ref(false);
const blankCreate = () => ({ owner_email: '', name: '', country: '', status: 'active' });
const createForm = ref(blankCreate());
const { errors: cErr, run: runCreate, clear: clearCreate } = useValidation(() => createForm.value, {
  owner_email: [email()],
  name: [required()],
  country: [iso2({ optional: true })]
});
const submitCreate = async () => {
  if (!runCreate()) return;
  creating.value = true;
  try {
    await platform.createStore(createForm.value);
    ui.success(t('platformPage.storeCreated'));
    showCreate.value = false;
    createForm.value = blankCreate();
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    creating.value = false;
  }
};

const setStatus = async (row, status) => {
  const prev = row.status;
  row.status = status;
  try {
    await platform.updateStore(row.id, { status });
    ui.success(t('platformPage.storeUpdated'));
  } catch (e) {
    row.status = prev;
    ui.error(errorMessage(e));
  }
};

// --- Per-store employee limit ----------------------------------------------
const showEmp = ref(false);
const savingEmp = ref(false);
const empStore = ref(null);
const empForm = ref(1);
const { errors: eErr, run: runEmp, clear: clearEmp } = useValidation(() => ({ max: empForm.value }), { max: [numberMin(1)] });
const openEmp = (row) => {
  empStore.value = row;
  empForm.value = row.max_employees ?? 1;
  showEmp.value = true;
};
const saveEmp = async () => {
  if (!runEmp()) return;
  savingEmp.value = true;
  try {
    const res = await platform.updateStore(empStore.value.id, { max_employees: Number(empForm.value) });
    const i = stores.value.findIndex((s) => s.id === res.data.id);
    if (i > -1) stores.value[i] = res.data;
    ui.success(t('platformPage.limitSaved'));
    showEmp.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingEmp.value = false;
  }
};

// --- Per-seller store limit ------------------------------------------------
const showStoreLimit = ref(false);
const savingSL = ref(false);
const slSeller = ref(null);
const slForm = ref(1);
const { errors: sErr, run: runSL, clear: clearSL } = useValidation(() => ({ max: slForm.value }), { max: [positive()] });
const openStoreLimit = (row) => {
  slSeller.value = row;
  slForm.value = row.max_stores ?? 1;
  showStoreLimit.value = true;
};
const saveStoreLimit = async () => {
  if (!runSL()) return;
  savingSL.value = true;
  try {
    const res = await platform.updateSeller(slSeller.value.id, { max_stores: Number(slForm.value) });
    const i = sellers.value.findIndex((s) => s.id === res.data.id);
    if (i > -1) sellers.value[i] = res.data;
    ui.success(t('platformPage.limitSaved'));
    showStoreLimit.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingSL.value = false;
  }
};

// --- Seller lookup (find a newly-contracted person by email) ----------------
const search = ref('');
const searching = ref(false);
const doSearch = async () => {
  searching.value = true;
  try {
    const sl = await platform.sellers(search.value.trim() ? { search: search.value.trim() } : {});
    sellers.value = sl.data || [];
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    searching.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <div v-if="loading" class="flex min-h-[50vh] items-center justify-center">
      <Spinner :size="30" :label="$t('platformPage.loadingPlatform')" />
    </div>

    <EmptyState
      v-else-if="!tenant.isPlatform"
      :icon="ShieldAlert"
      :title="$t('platformPage.adminsOnlyTitle')"
      :message="$t('platformPage.adminsOnlyMessage')"
    >
      <RouterLink :to="{ name: 'admin-dashboard' }" class="btn btn-primary btn-sm">{{ $t('platformPage.backToDashboard') }}</RouterLink>
    </EmptyState>

    <template v-else>
      <PageHeader :title="$t('platformPage.title')" :subtitle="$t('platformPage.subtitle')">
        <template #actions>
          <a href="/django-admin/" target="_blank" rel="noopener" class="btn btn-outline btn-sm">
            <ExternalLink class="h-4 w-4" /> {{ $t('platformPage.djangoAdmin') }}
          </a>
          <button class="btn btn-primary btn-sm" @click="showCreate = true">
            <Plus class="h-4 w-4" /> {{ $t('platformPage.createStoreForSeller') }}
          </button>
        </template>
      </PageHeader>

      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="k in kpis" :key="k.label" class="card p-5">
          <span class="grid h-10 w-10 place-items-center rounded-lg" :class="k.tone"><component :is="k.icon" class="h-5 w-5" /></span>
          <p class="mt-3 font-heading text-2xl font-bold">{{ k.value }}</p>
          <p class="text-sm text-muted">{{ k.label }}</p>
        </div>
      </div>

      <!-- Pending limit-increase requests -->
      <div v-if="requests.length" class="mt-8">
        <h2 class="section-title mb-4 flex items-center gap-2 text-xl">
          <Inbox class="h-5 w-5 text-amber-500" /> {{ $t('platformPage.requestsTitle') }}
          <span class="chip border-amber-200 bg-amber-50 text-amber-700">{{ requests.length }}</span>
        </h2>
        <DataTable :columns="requestColumns" :rows="requests">
          <template #cell-requester_email="{ row }">
            <div>
              <p class="font-medium text-ink">{{ row.requester_email }}</p>
              <p class="text-xs text-muted">{{ row.store_name || '—' }}</p>
            </div>
          </template>
          <template #cell-target="{ row }">
            <span class="chip border-slate-200 bg-slate-50 text-slate-700">
              {{ $t('platformPage.reqKind.' + row.kind) }}
              <span dir="ltr" class="font-semibold">{{ row.current_limit }} → {{ row.requested_limit }}</span>
            </span>
          </template>
          <template #cell-note="{ value }"><span class="text-sm text-muted">{{ value || '—' }}</span></template>
          <template #cell-actions="{ row }">
            <div class="flex justify-end gap-2">
              <button class="btn btn-primary btn-sm" :disabled="resolvingId === row.id" @click="resolveReq(row, true)"><Check class="h-4 w-4" /> {{ $t('platformPage.approve') }}</button>
              <button class="btn btn-ghost btn-sm text-rose-600" :disabled="resolvingId === row.id" @click="resolveReq(row, false)"><X class="h-4 w-4" /> {{ $t('platformPage.reject') }}</button>
            </div>
          </template>
        </DataTable>
      </div>

      <!-- All stores -->
      <div class="mt-8">
        <h2 class="section-title mb-4 text-xl">{{ $t('platformPage.allStoresTitle') }}</h2>
        <DataTable :columns="storeColumns" :rows="stores" :empty-title="$t('platformPage.emptyStoresTitle')" :empty-message="$t('platformPage.emptyStoresMessage')">
          <template #cell-name="{ row }">
            <div class="flex items-center gap-3">
              <span class="grid h-9 w-9 place-items-center rounded-lg bg-primary-50 text-primary-600"><StoreIcon class="h-4 w-4" /></span>
              <div>
                <p class="font-medium text-ink">{{ row.name }}</p>
                <p class="text-xs text-muted">{{ row.slug }}</p>
              </div>
            </div>
          </template>
          <template #cell-owner_email="{ value }"><span class="text-sm">{{ value }}</span></template>
          <template #cell-employees="{ row }">
            <button class="chip border-slate-200 bg-slate-50 text-slate-600 hover:border-primary-300" @click="openEmp(row)">
              <Users class="h-3.5 w-3.5" /> <span dir="ltr">{{ row.employee_count }} / {{ row.max_employees }}</span>
              <Pencil class="h-3 w-3 opacity-60" />
            </button>
          </template>
          <template #cell-status="{ row }">
            <select :value="row.status" class="input h-9 max-w-[150px] py-1 text-sm" @change="setStatus(row, $event.target.value)">
              <option v-for="s in STATUSES" :key="s" :value="s">{{ $t('platformPage.st.' + s) }}</option>
            </select>
          </template>
          <template #cell-actions="{ row }">
            <button class="btn btn-ghost btn-sm" @click="viewStorefront(row)"><Eye class="h-4 w-4" /> {{ $t('platformPage.view') }}</button>
          </template>
        </DataTable>
      </div>

      <!-- Sellers -->
      <div class="mt-10">
        <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="section-title text-xl">{{ $t('platformPage.sellersTitle') }}</h2>
          <div class="flex gap-2">
            <input
              v-model="search"
              class="input h-9 max-w-[220px] py-1 text-sm"
              :placeholder="$t('platformPage.searchByEmail')"
              @keyup.enter="doSearch"
            />
            <button class="btn btn-outline btn-sm" :disabled="searching" @click="doSearch"><Search class="h-4 w-4" /> {{ $t('platformPage.search') }}</button>
          </div>
        </div>
        <p class="mb-3 text-xs text-muted">{{ $t('platformPage.sellersNote') }}</p>
        <DataTable :columns="sellerColumns" :rows="sellers" :empty-title="$t('platformPage.noSellers')" :empty-message="$t('platformPage.noSellersMsg')">
          <template #cell-email="{ row }">
            <div class="flex items-center gap-3">
              <span class="grid h-9 w-9 place-items-center rounded-full bg-violet-100 text-sm font-semibold text-violet-700">
                {{ (row.email || '?').charAt(0).toUpperCase() }}
              </span>
              <span class="font-medium text-ink">{{ row.email }}</span>
            </div>
          </template>
          <template #cell-stores="{ row }">
            <span dir="ltr" class="chip border-slate-200 bg-slate-50 text-slate-600">{{ row.store_count }} / {{ row.max_stores }}</span>
          </template>
          <template #cell-actions="{ row }">
            <button class="btn btn-outline btn-sm" @click="openStoreLimit(row)"><Pencil class="h-4 w-4" /> {{ $t('platformPage.setStoreLimit') }}</button>
          </template>
        </DataTable>
      </div>

      <!-- Create store for seller -->
      <Modal v-model="showCreate" :title="$t('platformPage.createStoreForSeller')">
        <form id="pf-create" class="grid gap-4" novalidate @submit.prevent="submitCreate">
          <FormField v-model="createForm.owner_email" :label="$t('platformPage.ownerEmail')" type="email" placeholder="seller@example.com" :hint="$t('platformPage.ownerEmailHint')" :error="cErr.owner_email" @update:model-value="clearCreate('owner_email')" />
          <FormField v-model="createForm.name" :label="$t('platformPage.storeName')" :error="cErr.name" @update:model-value="clearCreate('name')" />
          <div class="grid grid-cols-2 gap-4">
            <FormField v-model="createForm.country" :label="$t('common.country')" placeholder="EG" :error="cErr.country" @update:model-value="clearCreate('country')" />
            <div>
              <label class="label">{{ $t('common.status') }}</label>
              <select v-model="createForm.status" class="input">
                <option v-for="s in STATUSES" :key="s" :value="s">{{ $t('platformPage.st.' + s) }}</option>
              </select>
            </div>
          </div>
        </form>
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="showCreate = false">{{ $t('common.cancel') }}</button>
            <button form="pf-create" type="submit" class="btn btn-primary" :disabled="creating">
              <Spinner v-if="creating" :size="18" /><span v-else>{{ $t('common.create') }}</span>
            </button>
          </div>
        </template>
      </Modal>

      <!-- Set employee limit -->
      <Modal v-model="showEmp" :title="$t('platformPage.setEmployeeLimit')" size="sm">
        <form id="pf-emp" class="grid gap-3" novalidate @submit.prevent="saveEmp">
          <p class="text-sm text-muted">{{ empStore?.name }}</p>
          <FormField v-model.number="empForm" :label="$t('platformPage.maxEmployees')" type="number" min="1" :error="eErr.max" @update:model-value="clearEmp('max')" />
        </form>
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="showEmp = false">{{ $t('common.cancel') }}</button>
            <button form="pf-emp" type="submit" class="btn btn-primary" :disabled="savingEmp">
              <Spinner v-if="savingEmp" :size="18" /><span v-else>{{ $t('common.save') }}</span>
            </button>
          </div>
        </template>
      </Modal>

      <!-- Set store limit for seller -->
      <Modal v-model="showStoreLimit" :title="$t('platformPage.setStoreLimit')" size="sm">
        <form id="pf-sl" class="grid gap-3" novalidate @submit.prevent="saveStoreLimit">
          <p class="text-sm text-muted">{{ slSeller?.email }}</p>
          <FormField v-model.number="slForm" :label="$t('platformPage.maxStores')" type="number" min="1" :hint="$t('platformPage.maxStoresHint')" :error="sErr.max" @update:model-value="clearSL('max')" />
        </form>
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="showStoreLimit = false">{{ $t('common.cancel') }}</button>
            <button form="pf-sl" type="submit" class="btn btn-primary" :disabled="savingSL">
              <Spinner v-if="savingSL" :size="18" /><span v-else>{{ $t('common.save') }}</span>
            </button>
          </div>
        </template>
      </Modal>
    </template>
  </div>
</template>
