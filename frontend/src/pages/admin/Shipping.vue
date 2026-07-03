<script setup>
import { ref, onMounted } from 'vue';
import { Plus, Truck, MapPin, Trash2 } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, required, numberMin } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const zones = ref([]);
const methodsByZone = ref({});

const loadMethods = async (zoneId) => {
  try {
    const res = await seller.shippingMethods(zoneId);
    methodsByZone.value = { ...methodsByZone.value, [zoneId]: res.data || [] };
  } catch {
    methodsByZone.value = { ...methodsByZone.value, [zoneId]: [] };
  }
};

const load = async () => {
  loading.value = true;
  try {
    const res = await seller.shippingZones();
    zones.value = res.data?.results || res.data || [];
    await Promise.all(zones.value.map((z) => loadMethods(z.id)));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

// Zone create
const zoneModal = ref(false);
const zoneBusy = ref(false);
const zoneForm = ref({ name: '', code: '', countries: '', is_default: false });
const { errors: zoneErrors, run: runZone, clear: clearZone } = useValidation(() => zoneForm.value, { name: [required()] });
const createZone = async () => {
  if (!runZone()) return;
  zoneBusy.value = true;
  try {
    const payload = {
      name: zoneForm.value.name,
      code: zoneForm.value.code || undefined,
      countries: zoneForm.value.countries ? zoneForm.value.countries.split(',').map((c) => c.trim().toUpperCase()).filter(Boolean) : [],
      is_default: zoneForm.value.is_default
    };
    await seller.createShippingZone(payload);
    ui.success(t('shippingPage.zoneCreated'));
    zoneModal.value = false;
    zoneForm.value = { name: '', code: '', countries: '', is_default: false };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    zoneBusy.value = false;
  }
};

// Method create
const methodModal = ref(false);
const methodBusy = ref(false);
const methodZone = ref(null);
const methodForm = ref({ name: '', price: 0, per_kg: 0, free_over: '', is_active: true });
const { errors: methodErrors, run: runMethod, clear: clearMethod } = useValidation(() => methodForm.value, { name: [required()], price: [numberMin(0)] });
const openMethod = (zone) => {
  methodZone.value = zone;
  methodForm.value = { name: '', price: 0, per_kg: 0, free_over: '', is_active: true };
  methodModal.value = true;
};
const createMethod = async () => {
  if (!runMethod()) return;
  methodBusy.value = true;
  try {
    const payload = { ...methodForm.value };
    if (payload.free_over === '' || payload.free_over == null) delete payload.free_over;
    await seller.createShippingMethod(methodZone.value.id, payload);
    ui.success(t('shippingPage.methodAdded'));
    methodModal.value = false;
    loadMethods(methodZone.value.id);
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    methodBusy.value = false;
  }
};

const deleteZone = async (zone) => {
  try {
    await seller.deleteShippingZone(zone.id);
    ui.success(t('shippingPage.zoneDeleted'));
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) load();
  else loading.value = false;
});
</script>

<template>
  <div>
    <PageHeader :title="$t('shippingPage.title')" :subtitle="$t('shippingPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="zoneModal = true"><Plus class="h-4 w-4" /> {{ $t('shippingPage.addZone') }}</button>
      </template>
    </PageHeader>

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="28" :label="$t('common.loading')" /></div>

    <div v-else-if="zones.length" class="grid gap-5 lg:grid-cols-2">
      <div v-for="z in zones" :key="z.id" class="card p-5">
        <div class="mb-4 flex items-start justify-between">
          <div>
            <h3 class="flex items-center gap-2 font-heading text-lg font-bold"><MapPin class="h-5 w-5 text-primary-600" /> {{ z.name }}</h3>
            <p class="mt-1 text-xs text-muted">{{ (z.countries || []).join(', ') || $t('shippingPage.allCountries') }}</p>
          </div>
          <div class="flex items-center gap-2">
            <StatusBadge v-if="z.is_default" status="active" :label="$t('shippingPage.default')" />
            <button v-if="tenant.canWrite" class="text-slate-400 hover:text-secondary-500" @click="deleteZone(z)"><Trash2 class="h-4 w-4" /></button>
          </div>
        </div>

        <ul v-if="methodsByZone[z.id]?.length" class="space-y-2">
          <li v-for="m in methodsByZone[z.id]" :key="m.id" class="flex items-center justify-between rounded-lg bg-lightbg px-3 py-2 text-sm">
            <span class="flex items-center gap-2"><Truck class="h-4 w-4 text-primary-600" /> {{ m.name }}</span>
            <span class="font-medium">{{ Number(m.price) > 0 ? `${m.price} ${tenant.currency}` : $t('shippingPage.free') }}<span v-if="Number(m.free_over) > 0" class="ms-1 text-xs text-muted">· {{ $t('shippingPage.freeOver', { amount: m.free_over }) }}</span></span>
          </li>
        </ul>
        <p v-else class="rounded-lg bg-lightbg px-3 py-2 text-sm text-muted">{{ $t('shippingPage.noMethods') }}</p>

        <button v-if="tenant.canWrite" class="btn btn-outline btn-sm mt-4" @click="openMethod(z)"><Plus class="h-4 w-4" /> {{ $t('shippingPage.addMethod') }}</button>
      </div>
    </div>

    <EmptyState v-else :icon="Truck" :title="$t('shippingPage.emptyTitle')" :message="$t('shippingPage.emptyMsg')">
      <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="zoneModal = true">{{ $t('shippingPage.addZone') }}</button>
    </EmptyState>

    <!-- Zone modal -->
    <Modal v-model="zoneModal" :title="$t('shippingPage.newZone')">
      <form id="zone-form" class="grid gap-4" novalidate @submit.prevent="createZone">
        <FormField v-model="zoneForm.name" :label="$t('shippingPage.zoneName')" placeholder="Domestic" required :error="zoneErrors.name" @update:model-value="clearZone('name')" />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="zoneForm.code" :label="$t('shippingPage.code')" placeholder="DOM" />
          <FormField v-model="zoneForm.countries" :label="$t('shippingPage.countries')" placeholder="US, CA" />
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="zoneForm.is_default" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('shippingPage.defaultZone') }}</label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="zoneModal = false">{{ $t('common.cancel') }}</button>
          <button form="zone-form" type="submit" class="btn btn-primary" :disabled="zoneBusy"><Spinner v-if="zoneBusy" :size="18" /><span v-else>{{ $t('shippingPage.createZone') }}</span></button>
        </div>
      </template>
    </Modal>

    <!-- Method modal -->
    <Modal v-model="methodModal" :title="$t('shippingPage.addMethod') + (methodZone ? ` · ${methodZone.name}` : '')">
      <form id="method-form" class="grid gap-4" novalidate @submit.prevent="createMethod">
        <FormField v-model="methodForm.name" :label="$t('shippingPage.methodName')" placeholder="Standard" required :error="methodErrors.name" @update:model-value="clearMethod('name')" />
        <div class="grid grid-cols-3 gap-4">
          <FormField v-model.number="methodForm.price" :label="$t('common.price')" type="number" step="0.01" :error="methodErrors.price" @update:model-value="clearMethod('price')" />
          <FormField v-model.number="methodForm.per_kg" :label="$t('shippingPage.perKg')" type="number" step="0.01" />
          <FormField v-model="methodForm.free_over" :label="$t('shippingPage.freeOverLabel')" type="number" step="0.01" placeholder="—" />
        </div>
        <label class="flex items-center gap-2 text-sm"><input v-model="methodForm.is_active" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('common.active') }}</label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="methodModal = false">{{ $t('common.cancel') }}</button>
          <button form="method-form" type="submit" class="btn btn-primary" :disabled="methodBusy"><Spinner v-if="methodBusy" :size="18" /><span v-else>{{ $t('shippingPage.addMethod') }}</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
