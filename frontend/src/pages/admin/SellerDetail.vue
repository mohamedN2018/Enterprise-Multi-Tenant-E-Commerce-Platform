<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  ArrowLeft,
  Store as StoreIcon,
  Package,
  Users,
  Eye,
  LogIn,
  Pencil,
  Plus,
  ShieldCheck,
  ShieldAlert,
  Layers
} from 'lucide-vue-next';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { platform } from '@/services/platform';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, numberMin, positive, required, iso2 } from '@/utils/validators';

const route = useRoute();
const router = useRouter();
const tenant = useTenantStore();
const ui = useUiStore();

const STATUSES = ['draft', 'active', 'suspended', 'closed'];
const loading = ref(true);
const seller = ref(null);
const stores = ref([]);

const load = async () => {
  loading.value = true;
  try {
    await tenant.ensureReady();
    if (!tenant.isPlatform) return;
    const res = await platform.seller(route.params.id);
    seller.value = res.data;
    stores.value = res.data?.stores || [];
  } catch (e) {
    ui.error(errorMessage(e));
    seller.value = null;
  } finally {
    loading.value = false;
  }
};

const totals = computed(() => ({
  stores: stores.value.length,
  products: stores.value.reduce((a, s) => a + (s.product_count || 0), 0),
  employees: stores.value.reduce((a, s) => a + (s.employee_count || 0), 0)
}));

const joined = computed(() => (seller.value?.created_at || '').slice(0, 10));

const backToPanel = () => router.push({ name: 'admin-platform' });

const enterStore = (s) => {
  tenant.select(s.id);
  router.push({ name: 'admin-dashboard' }).then(() => router.go(0)).catch(() => router.go(0));
};
const viewStorefront = (s) => window.open(`/products?store=${s.slug}`, '_blank', 'noopener');

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

// --- Employee limit -------------------------------------------------------
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

// --- Store limit (for this seller) ----------------------------------------
const showSL = ref(false);
const savingSL = ref(false);
const slForm = ref(1);
const { errors: sErr, run: runSL, clear: clearSL } = useValidation(() => ({ max: slForm.value }), { max: [positive()] });
const openSL = () => {
  slForm.value = seller.value?.max_stores ?? 1;
  showSL.value = true;
};
const saveSL = async () => {
  if (!runSL()) return;
  savingSL.value = true;
  try {
    const res = await platform.updateSeller(seller.value.id, { max_stores: Number(slForm.value) });
    seller.value.max_stores = res.data.max_stores;
    ui.success(t('platformPage.limitSaved'));
    showSL.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingSL.value = false;
  }
};

// --- Create a store for this seller ---------------------------------------
const showCreate = ref(false);
const creating = ref(false);
const blankCreate = () => ({ owner_email: '', name: '', country: '', status: 'active' });
const createForm = ref(blankCreate());
const { errors: cErr, run: runCreate, clear: clearCreate } = useValidation(() => createForm.value, {
  name: [required()],
  country: [iso2({ optional: true })]
});
const openCreate = () => {
  createForm.value = { ...blankCreate(), owner_email: seller.value?.email || '' };
  showCreate.value = true;
};
const submitCreate = async () => {
  if (!runCreate()) return;
  creating.value = true;
  try {
    await platform.createStore(createForm.value);
    ui.success(t('platformPage.storeCreated'));
    showCreate.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    creating.value = false;
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
    />

    <template v-else-if="!seller">
      <button class="btn btn-ghost btn-sm mb-4" @click="backToPanel"><ArrowLeft class="h-4 w-4 rtl:rotate-180" /> {{ $t('admin.backToPanel') }}</button>
      <EmptyState :icon="ShieldAlert" :title="$t('platformPage.sellerNotFound')" :message="$t('platformPage.emptyStoresMessage')" />
    </template>

    <template v-else>
      <button class="btn btn-ghost btn-sm mb-4" @click="backToPanel"><ArrowLeft class="h-4 w-4 rtl:rotate-180" /> {{ $t('admin.backToPanel') }}</button>

      <!-- Seller header -->
      <div class="card flex flex-wrap items-center gap-4 p-5">
        <span class="grid h-14 w-14 shrink-0 place-items-center rounded-full bg-violet-100 text-lg font-bold text-violet-700">{{ (seller.email || '?').charAt(0).toUpperCase() }}</span>
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="truncate font-heading text-xl font-bold text-ink">{{ seller.email }}</h1>
            <span v-if="seller.is_active" class="chip border-emerald-200 bg-emerald-50 text-emerald-700"><ShieldCheck class="h-3 w-3" /> {{ $t('platformPage.accountActive') }}</span>
            <span v-else class="chip border-rose-200 bg-rose-50 text-rose-700"><ShieldAlert class="h-3 w-3" /> {{ $t('platformPage.accountInactive') }}</span>
          </div>
          <p class="mt-0.5 text-sm text-muted">{{ $t('platformPage.owner') }} · {{ $t('platformPage.joined') }} {{ joined }}</p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-outline btn-sm" @click="openSL"><Pencil class="h-4 w-4" /> {{ $t('platformPage.setStoreLimit') }}</button>
          <button class="btn btn-primary btn-sm" @click="openCreate"><Plus class="h-4 w-4" /> {{ $t('platformPage.createStoreForSeller') }}</button>
        </div>
      </div>

      <!-- KPIs -->
      <div class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="card p-5"><span class="grid h-10 w-10 place-items-center rounded-lg bg-primary-50 text-primary-600"><StoreIcon class="h-5 w-5" /></span><p class="mt-3 font-heading text-2xl font-bold" dir="ltr">{{ totals.stores }} / {{ seller.max_stores }}</p><p class="text-sm text-muted">{{ $t('platformPage.ownedStores') }}</p></div>
        <div class="card p-5"><span class="grid h-10 w-10 place-items-center rounded-lg bg-amber-50 text-amber-600"><Package class="h-5 w-5" /></span><p class="mt-3 font-heading text-2xl font-bold">{{ totals.products }}</p><p class="text-sm text-muted">{{ $t('platformPage.totalProducts') }}</p></div>
        <div class="card p-5"><span class="grid h-10 w-10 place-items-center rounded-lg bg-sky-50 text-sky-600"><Users class="h-5 w-5" /></span><p class="mt-3 font-heading text-2xl font-bold">{{ totals.employees }}</p><p class="text-sm text-muted">{{ $t('platformPage.employees') }}</p></div>
        <div class="card p-5"><span class="grid h-10 w-10 place-items-center rounded-lg bg-violet-50 text-violet-600"><Layers class="h-5 w-5" /></span><p class="mt-3 font-heading text-2xl font-bold">{{ seller.max_stores }}</p><p class="text-sm text-muted">{{ $t('platformPage.maxStores') }}</p></div>
      </div>

      <!-- Stores -->
      <h2 class="section-title mb-4 mt-8 text-xl">{{ $t('platformPage.ownedStores') }}</h2>
      <div v-if="stores.length" class="card divide-y divide-slate-100 p-0 dark:divide-slate-800">
        <div v-for="st in stores" :key="st.id" class="flex flex-wrap items-center gap-3 px-4 py-3">
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
      <EmptyState v-else :icon="StoreIcon" :title="$t('platformPage.noStoresForSeller')" :message="$t('platformPage.emptyStoresMessage')">
        <button class="btn btn-primary btn-sm" @click="openCreate"><Plus class="h-4 w-4" /> {{ $t('platformPage.createStoreForSeller') }}</button>
      </EmptyState>

      <!-- Employee limit modal -->
      <Modal v-model="showEmp" :title="$t('platformPage.setEmployeeLimit')" size="sm">
        <form id="sd-emp" class="grid gap-3" novalidate @submit.prevent="saveEmp">
          <p class="text-sm text-muted">{{ empStore?.name }}</p>
          <FormField v-model.number="empForm" :label="$t('platformPage.maxEmployees')" type="number" min="1" :error="eErr.max" @update:model-value="clearEmp('max')" />
        </form>
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="showEmp = false">{{ $t('common.cancel') }}</button>
            <button form="sd-emp" type="submit" class="btn btn-primary" :disabled="savingEmp"><Spinner v-if="savingEmp" :size="18" /><span v-else>{{ $t('common.save') }}</span></button>
          </div>
        </template>
      </Modal>

      <!-- Store limit modal -->
      <Modal v-model="showSL" :title="$t('platformPage.setStoreLimit')" size="sm">
        <form id="sd-sl" class="grid gap-3" novalidate @submit.prevent="saveSL">
          <p class="text-sm text-muted">{{ seller.email }}</p>
          <FormField v-model.number="slForm" :label="$t('platformPage.maxStores')" type="number" min="1" :hint="$t('platformPage.maxStoresHint')" :error="sErr.max" @update:model-value="clearSL('max')" />
        </form>
        <template #footer>
          <div class="flex justify-end gap-2">
            <button class="btn btn-ghost" @click="showSL = false">{{ $t('common.cancel') }}</button>
            <button form="sd-sl" type="submit" class="btn btn-primary" :disabled="savingSL"><Spinner v-if="savingSL" :size="18" /><span v-else>{{ $t('common.save') }}</span></button>
          </div>
        </template>
      </Modal>

      <!-- Create store modal -->
      <Modal v-model="showCreate" :title="$t('platformPage.createStoreForSeller')">
        <form id="sd-create" class="grid gap-4" novalidate @submit.prevent="submitCreate">
          <FormField v-model="createForm.owner_email" :label="$t('platformPage.ownerEmail')" type="email" disabled />
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
            <button form="sd-create" type="submit" class="btn btn-primary" :disabled="creating"><Spinner v-if="creating" :size="18" /><span v-else>{{ $t('common.create') }}</span></button>
          </div>
        </template>
      </Modal>
    </template>
  </div>
</template>
