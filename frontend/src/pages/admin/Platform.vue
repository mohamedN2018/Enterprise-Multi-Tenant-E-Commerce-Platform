<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
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
  X,
  LogIn,
  UserPlus,
  Package
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
import { useValidation, required, email, iso2, numberMin, positive, min } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();
const router = useRouter();

// Enter a store to manage it (as its owner). The admin thereby leaves the
// platform panel and drops into full store management for that store.
const enterStore = (s) => {
  tenant.select(s.id);
  router.push({ name: 'admin-dashboard' }).then(() => router.go(0)).catch(() => router.go(0));
};

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
  { label: t('platformPage.sellers'), value: ownerGroups.value.length, icon: UserCog, tone: 'text-violet-600 bg-violet-50' },
  { label: t('platformPage.totalProducts'), value: stores.value.reduce((a, s) => a + (s.product_count || 0), 0), icon: Package, tone: 'text-amber-600 bg-amber-50' },
  { label: t('platformPage.employees'), value: stores.value.reduce((a, s) => a + (s.employee_count || 0), 0), icon: Users, tone: 'text-sky-600 bg-sky-50' }
]);

// Group every store under its owner (seller), so the admin sees each seller and
// the stores they own beneath them. Seeded from the sellers list so a freshly
// created seller with no store yet still appears.
const ownerGroups = computed(() => {
  const byEmail = new Map();
  for (const s of sellers.value) {
    byEmail.set(s.email, { email: s.email, sellerId: s.id, maxStores: s.max_stores, stores: [] });
  }
  for (const st of stores.value) {
    let g = byEmail.get(st.owner_email);
    if (!g) {
      g = { email: st.owner_email, sellerId: st.owner_id, maxStores: st.owner_max_stores, stores: [] };
      byEmail.set(st.owner_email, g);
    }
    if (!g.sellerId) g.sellerId = st.owner_id;
    if (g.maxStores == null) g.maxStores = st.owner_max_stores;
    g.stores.push(st);
  }
  return [...byEmail.values()].sort(
    (a, b) => b.stores.length - a.stores.length || (a.email || '').localeCompare(b.email || '')
  );
});

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

// Open the create-store modal pre-filled for a specific seller.
const openCreateForSeller = (ownerEmail) => {
  createForm.value = { ...blankCreate(), owner_email: ownerEmail };
  showCreate.value = true;
};

// --- Create a seller account (with the default one store) ------------------
const showSeller = ref(false);
const creatingSeller = ref(false);
const blankSeller = () => ({ email: '', password: '', store_name: '', country: '' });
const sellerForm = ref(blankSeller());
const { errors: seErr, run: runSeller, clear: clearSeller } = useValidation(() => sellerForm.value, {
  email: [email()],
  password: [min(8)],
  country: [iso2({ optional: true })]
});
const submitSeller = async () => {
  if (!runSeller()) return;
  creatingSeller.value = true;
  try {
    await platform.createSeller(sellerForm.value);
    ui.success(t('platformPage.sellerCreated'));
    showSeller.value = false;
    sellerForm.value = blankSeller();
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    creatingSeller.value = false;
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
    await platform.updateSeller(slSeller.value.id, { max_stores: Number(slForm.value) });
    ui.success(t('platformPage.limitSaved'));
    showStoreLimit.value = false;
    load(); // refresh so the grouped seller→stores view shows the new cap
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
          <a href="/django-admin/" target="_blank" rel="noopener" class="btn btn-ghost btn-sm">
            <ExternalLink class="h-4 w-4" /> {{ $t('platformPage.djangoAdmin') }}
          </a>
          <button class="btn btn-outline btn-sm" @click="showCreate = true">
            <Plus class="h-4 w-4" /> {{ $t('platformPage.createStoreForSeller') }}
          </button>
          <button class="btn btn-primary btn-sm" @click="showSeller = true">
            <UserPlus class="h-4 w-4" /> {{ $t('platformPage.createSeller') }}
          </button>
        </template>
      </PageHeader>

      <!-- KPIs -->
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
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

      <!-- Sellers & their stores (owner → stores hierarchy) -->
      <div class="mt-8">
        <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h2 class="section-title text-xl">{{ $t('platformPage.sellersStoresTitle') }}</h2>
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
        <p class="mb-4 text-xs text-muted">{{ $t('platformPage.sellersStoresNote') }}</p>

        <div class="space-y-4">
          <div v-for="g in ownerGroups" :key="g.email" class="card overflow-hidden p-0">
            <!-- Owner (seller) header -->
            <div class="flex flex-wrap items-center gap-3 border-b border-slate-100 bg-slate-50/70 px-4 py-3 dark:border-slate-800 dark:bg-slate-800/40">
              <span class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-violet-100 text-sm font-semibold text-violet-700">{{ (g.email || '?').charAt(0).toUpperCase() }}</span>
              <div class="min-w-0 flex-1">
                <p class="truncate font-semibold text-ink">{{ g.email }}</p>
                <p class="text-xs text-muted">{{ $t('platformPage.owner') }}</p>
              </div>
              <span dir="ltr" class="chip border-slate-200 bg-white text-slate-600 dark:bg-slate-900"><StoreIcon class="h-3.5 w-3.5" /> {{ g.stores.length }} / {{ g.maxStores }}</span>
              <button class="btn btn-outline btn-sm" @click="openStoreLimit({ id: g.sellerId, email: g.email, max_stores: g.maxStores })"><Pencil class="h-4 w-4" /> {{ $t('platformPage.setStoreLimit') }}</button>
            </div>

            <!-- Their stores -->
            <div v-if="g.stores.length" class="divide-y divide-slate-100 dark:divide-slate-800">
              <div v-for="st in g.stores" :key="st.id" class="flex flex-wrap items-center gap-3 px-4 py-3">
                <span class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary-50 text-primary-600"><StoreIcon class="h-4 w-4" /></span>
                <div class="min-w-0 flex-1">
                  <p class="truncate font-medium text-ink">{{ st.name }}</p>
                  <p class="text-xs text-muted">{{ st.slug }}</p>
                </div>
                <span dir="ltr" class="chip border-amber-200 bg-amber-50 text-amber-700" :title="$t('platformPage.totalProducts')"><Package class="h-3.5 w-3.5" /> {{ st.product_count ?? 0 }}</span>
                <button class="chip border-slate-200 bg-slate-50 text-slate-600 hover:border-primary-300" :title="$t('platformPage.setEmployeeLimit')" @click="openEmp(st)"><Users class="h-3.5 w-3.5" /> <span dir="ltr">{{ st.employee_count }} / {{ st.max_employees }}</span> <Pencil class="h-3 w-3 opacity-60" /></button>
                <select :value="st.status" class="input h-9 max-w-[140px] py-1 text-sm" @change="setStatus(st, $event.target.value)">
                  <option v-for="s in STATUSES" :key="s" :value="s">{{ $t('platformPage.st.' + s) }}</option>
                </select>
                <button class="btn btn-primary btn-sm" :title="$t('platformPage.manageHint')" @click="enterStore(st)"><LogIn class="h-4 w-4" /> {{ $t('platformPage.manage') }}</button>
                <button class="btn btn-ghost btn-sm" @click="viewStorefront(st)"><Eye class="h-4 w-4" /> {{ $t('platformPage.view') }}</button>
              </div>
            </div>
            <div v-else class="flex flex-wrap items-center gap-2 px-4 py-3 text-sm text-muted">
              {{ $t('platformPage.noStoresForSeller') }}
              <button class="btn btn-outline btn-sm" @click="openCreateForSeller(g.email)"><Plus class="h-4 w-4" /> {{ $t('platformPage.createStoreForSeller') }}</button>
            </div>
          </div>

          <EmptyState v-if="!ownerGroups.length" :icon="StoreIcon" :title="$t('platformPage.emptyStoresTitle')" :message="$t('platformPage.emptyStoresMessage')" />
        </div>
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

      <!-- Create seller account (+ default store) -->
      <Modal v-model="showSeller" :title="$t('platformPage.createSeller')">
        <form id="pf-seller" class="grid gap-4" novalidate @submit.prevent="submitSeller">
          <p class="rounded-lg bg-primary-50 px-3 py-2 text-xs text-primary-700 dark:bg-primary-500/10">
            {{ $t('platformPage.createSellerNote') }}
          </p>
          <FormField v-model="sellerForm.email" :label="$t('platformPage.sellerEmail')" type="email" placeholder="seller@example.com" :error="seErr.email" @update:model-value="clearSeller('email')" />
          <FormField v-model="sellerForm.password" :label="$t('platformPage.tempPassword')" type="password" autocomplete="new-password" :hint="$t('platformPage.tempPasswordHint')" :error="seErr.password" @update:model-value="clearSeller('password')" />
          <div class="grid grid-cols-2 gap-4">
            <FormField v-model="sellerForm.store_name" :label="$t('platformPage.storeNameOptional')" :hint="$t('platformPage.storeNameOptionalHint')" />
            <FormField v-model="sellerForm.country" :label="$t('common.country')" placeholder="EG" :error="seErr.country" @update:model-value="clearSeller('country')" />
          </div>
        </form>
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="showSeller = false">{{ $t('common.cancel') }}</button>
            <button form="pf-seller" type="submit" class="btn btn-primary" :disabled="creatingSeller">
              <Spinner v-if="creatingSeller" :size="18" /><span v-else>{{ $t('platformPage.createSeller') }}</span>
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
