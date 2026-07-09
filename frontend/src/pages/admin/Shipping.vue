<script setup>
import { ref, computed, onMounted } from 'vue';
import { Plus, Truck, MapPin, Trash2, Globe, Map as MapIcon, Minus } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import Spinner from '@/components/ui/Spinner.vue';
import StatusBadge from '@/components/ui/StatusBadge.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import DeliveryMap from '@/components/DeliveryMap.vue';
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

// Zone create — country OR map (circle) zone.
const zoneModal = ref(false);
const zoneBusy = ref(false);
const zoneType = ref('map');
const zoneForm = ref({ name: '', code: '', countries: '', is_default: false });
const zonePoint = ref(null); // { lat, lng }
const zoneRadius = ref(5);
const { errors: zoneErrors, run: runZone, clear: clearZone } = useValidation(() => zoneForm.value, { name: [required()] });

const openZone = () => {
  zoneType.value = 'map';
  zoneForm.value = { name: '', code: '', countries: '', is_default: false };
  zonePoint.value = null;
  zoneRadius.value = 5;
  zoneModal.value = true;
};

const createZone = async () => {
  if (!runZone()) return;
  if (zoneType.value === 'map' && !zonePoint.value) {
    ui.error(t('shippingPage.pickCenter'));
    return;
  }
  zoneBusy.value = true;
  try {
    const payload = { name: zoneForm.value.name, code: zoneForm.value.code || undefined };
    if (zoneType.value === 'map') {
      payload.center_lat = Number(zonePoint.value.lat.toFixed(6));
      payload.center_lng = Number(zonePoint.value.lng.toFixed(6));
      payload.radius_km = Number(zoneRadius.value);
    } else {
      payload.countries = zoneForm.value.countries
        ? zoneForm.value.countries.split(',').map((c) => c.trim().toUpperCase()).filter(Boolean)
        : [];
      payload.is_default = zoneForm.value.is_default;
    }
    await seller.createShippingZone(payload);
    ui.success(t('shippingPage.zoneCreated'));
    zoneModal.value = false;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    zoneBusy.value = false;
  }
};

// Resize a map zone in place (enlarge / shrink the circle).
const resizeZone = async (zone, delta) => {
  const next = Math.max(0.5, Math.round((Number(zone.radius_km) + delta) * 10) / 10);
  const prev = zone.radius_km;
  zone.radius_km = next; // optimistic
  try {
    await seller.updateShippingZone(zone.id, { radius_km: next });
  } catch (e) {
    zone.radius_km = prev;
    ui.error(errorMessage(e));
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

const useMyLocation = () => {
  if (!navigator.geolocation) return ui.error(t('shippingPage.geoUnsupported'));
  navigator.geolocation.getCurrentPosition(
    (pos) => (zonePoint.value = { lat: pos.coords.latitude, lng: pos.coords.longitude }),
    () => ui.error(t('shippingPage.geoDenied'))
  );
};

// All existing map zones drawn together on the overview map.
const geoCircles = computed(() =>
  zones.value
    .filter((z) => z.is_geo)
    .map((z) => ({ lat: Number(z.center_lat), lng: Number(z.center_lng), radius_km: Number(z.radius_km), name: z.name }))
);
const overviewCenter = computed(() => (geoCircles.value[0] ? { lat: geoCircles.value[0].lat, lng: geoCircles.value[0].lng } : undefined));

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
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="openZone"><Plus class="h-4 w-4" /> {{ $t('shippingPage.addZone') }}</button>
      </template>
    </PageHeader>

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="28" :label="$t('common.loading')" /></div>

    <template v-else-if="zones.length">
      <!-- Coverage overview map -->
      <div v-if="geoCircles.length" class="card mb-5 p-4">
        <h3 class="mb-3 flex items-center gap-2 font-heading text-sm font-bold text-ink"><MapIcon class="h-4 w-4 text-primary-600" /> {{ $t('shippingPage.coverageMap') }}</h3>
        <DeliveryMap :circles="geoCircles" :center="overviewCenter" :zoom="10" height="300px" />
      </div>

      <div class="grid gap-5 lg:grid-cols-2">
        <div v-for="z in zones" :key="z.id" class="card p-5">
          <div class="mb-4 flex items-start justify-between">
            <div>
              <h3 class="flex items-center gap-2 font-heading text-lg font-bold">
                <component :is="z.is_geo ? MapIcon : Globe" class="h-5 w-5 text-primary-600" /> {{ z.name }}
              </h3>
              <p v-if="z.is_geo" class="mt-1 text-xs text-muted">{{ $t('shippingPage.radiusLabel', { km: z.radius_km }) }}</p>
              <p v-else class="mt-1 text-xs text-muted">{{ (z.countries || []).join(', ') || $t('shippingPage.allCountries') }}</p>
            </div>
            <div class="flex items-center gap-2">
              <StatusBadge v-if="z.is_geo" status="active" :label="$t('shippingPage.mapZone')" />
              <StatusBadge v-else-if="z.is_default" status="active" :label="$t('shippingPage.default')" />
              <button v-if="tenant.canWrite" class="text-slate-400 hover:text-secondary-500" @click="deleteZone(z)"><Trash2 class="h-4 w-4" /></button>
            </div>
          </div>

          <!-- Map zone: mini preview + resize controls -->
          <div v-if="z.is_geo" class="mb-4">
            <DeliveryMap
              :circles="[{ lat: Number(z.center_lat), lng: Number(z.center_lng), radius_km: Number(z.radius_km), name: z.name }]"
              :center="{ lat: Number(z.center_lat), lng: Number(z.center_lng) }"
              :zoom="11"
              height="180px"
            />
            <div v-if="tenant.canWrite" class="mt-3 flex items-center justify-center gap-3">
              <button class="grid h-8 w-8 place-items-center rounded-full border border-slate-200 hover:border-primary-500 hover:text-primary-600 dark:border-slate-700" :title="$t('shippingPage.shrink')" @click="resizeZone(z, -1)"><Minus class="h-4 w-4" /></button>
              <span class="min-w-[86px] text-center text-sm font-semibold">{{ z.radius_km }} {{ $t('shippingPage.km') }}</span>
              <button class="grid h-8 w-8 place-items-center rounded-full border border-slate-200 hover:border-primary-500 hover:text-primary-600 dark:border-slate-700" :title="$t('shippingPage.enlarge')" @click="resizeZone(z, 1)"><Plus class="h-4 w-4" /></button>
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
    </template>

    <EmptyState v-else :icon="Truck" :title="$t('shippingPage.emptyTitle')" :message="$t('shippingPage.emptyMsg')">
      <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="openZone">{{ $t('shippingPage.addZone') }}</button>
    </EmptyState>

    <!-- Zone modal -->
    <Modal v-model="zoneModal" :title="$t('shippingPage.newZone')" size="lg">
      <form id="zone-form" class="grid gap-4" novalidate @submit.prevent="createZone">
        <!-- Zone type toggle -->
        <div class="grid grid-cols-2 gap-2">
          <button type="button" class="flex items-center justify-center gap-2 rounded-xl border p-3 text-sm font-medium transition" :class="zoneType === 'map' ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-600/10' : 'border-slate-200 dark:border-slate-700'" @click="zoneType = 'map'">
            <MapIcon class="h-4 w-4" /> {{ $t('shippingPage.mapZone') }}
          </button>
          <button type="button" class="flex items-center justify-center gap-2 rounded-xl border p-3 text-sm font-medium transition" :class="zoneType === 'country' ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-600/10' : 'border-slate-200 dark:border-slate-700'" @click="zoneType = 'country'">
            <Globe class="h-4 w-4" /> {{ $t('shippingPage.countryZone') }}
          </button>
        </div>

        <FormField v-model="zoneForm.name" :label="$t('shippingPage.zoneName')" :placeholder="zoneType === 'map' ? $t('shippingPage.mapZonePlaceholder') : 'Domestic'" required :error="zoneErrors.name" @update:model-value="clearZone('name')" />

        <!-- Map zone editor -->
        <div v-if="zoneType === 'map'" class="grid gap-3">
          <div class="flex items-center justify-between">
            <p class="text-sm text-muted">{{ zonePoint ? $t('shippingPage.centerSet') : $t('shippingPage.pickCenter') }}</p>
            <button type="button" class="btn btn-ghost btn-sm" @click="useMyLocation"><MapPin class="h-4 w-4" /> {{ $t('shippingPage.useMyLocation') }}</button>
          </div>
          <DeliveryMap v-model="zonePoint" editable :radius-km="zoneRadius" height="300px" />
          <div>
            <label class="mb-1 flex items-center justify-between text-sm">
              <span class="font-medium">{{ $t('shippingPage.radius') }}</span>
              <span class="font-semibold text-primary-600">{{ zoneRadius }} {{ $t('shippingPage.km') }}</span>
            </label>
            <input v-model.number="zoneRadius" type="range" min="0.5" max="100" step="0.5" class="w-full accent-primary-600" />
          </div>
        </div>

        <!-- Country zone -->
        <template v-else>
          <div class="grid grid-cols-2 gap-4">
            <FormField v-model="zoneForm.code" :label="$t('shippingPage.code')" placeholder="DOM" />
            <FormField v-model="zoneForm.countries" :label="$t('shippingPage.countries')" placeholder="EG, SA" />
          </div>
          <label class="flex items-center gap-2 text-sm"><input v-model="zoneForm.is_default" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('shippingPage.defaultZone') }}</label>
        </template>
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
