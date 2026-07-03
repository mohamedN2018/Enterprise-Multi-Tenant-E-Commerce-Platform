<script setup>
import { ref, onMounted } from 'vue';
import { Plus, Tag } from 'lucide-vue-next';
import { t } from '@/i18n';
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

const tenant = useTenantStore();
const ui = useUiStore();

const loading = ref(true);
const attributes = ref([]);
const valuesByAttr = ref({});

const loadValues = async (attrId) => {
  try {
    const res = await seller.attributeValues(attrId);
    valuesByAttr.value = { ...valuesByAttr.value, [attrId]: res.data?.results || res.data || [] };
  } catch {
    valuesByAttr.value = { ...valuesByAttr.value, [attrId]: [] };
  }
};

const load = async () => {
  loading.value = true;
  try {
    const res = await seller.attributes();
    attributes.value = res.data?.results || res.data || [];
    await Promise.all(attributes.value.map((a) => loadValues(a.id)));
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const attrModal = ref(false);
const attrBusy = ref(false);
const attrForm = ref({ name: '', code: '', is_variant: true, sort_order: 0 });
const createAttr = async () => {
  attrBusy.value = true;
  try {
    const payload = { ...attrForm.value };
    if (!payload.code) delete payload.code;
    await seller.createAttribute(payload);
    ui.success(t('attributesPage.attributeCreated'));
    attrModal.value = false;
    attrForm.value = { name: '', code: '', is_variant: true, sort_order: 0 };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    attrBusy.value = false;
  }
};

const valModal = ref(false);
const valBusy = ref(false);
const valAttr = ref(null);
const valForm = ref({ value: '', label: '', sort_order: 0 });
const openVal = (attr) => {
  valAttr.value = attr;
  valForm.value = { value: '', label: '', sort_order: 0 };
  valModal.value = true;
};
const createVal = async () => {
  valBusy.value = true;
  try {
    await seller.createAttributeValue(valAttr.value.id, valForm.value);
    ui.success(t('attributesPage.valueAdded'));
    valModal.value = false;
    loadValues(valAttr.value.id);
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    valBusy.value = false;
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
    <PageHeader :title="$t('attributesPage.title')" :subtitle="$t('attributesPage.subtitle')">
      <template #actions>
        <span v-if="!tenant.canWrite" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('common.readOnly') }}</span>
        <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="attrModal = true"><Plus class="h-4 w-4" /> {{ $t('attributesPage.addAttribute') }}</button>
      </template>
    </PageHeader>

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="28" :label="$t('common.loading')" /></div>

    <div v-else-if="attributes.length" class="grid gap-5 lg:grid-cols-2">
      <div v-for="a in attributes" :key="a.id" class="card p-5">
        <div class="mb-3 flex items-start justify-between">
          <div>
            <h3 class="flex items-center gap-2 font-heading text-lg font-bold"><Tag class="h-5 w-5 text-primary-600" /> {{ a.name }}</h3>
            <p class="text-xs text-muted">{{ a.code }}</p>
          </div>
          <StatusBadge :status="a.is_variant ? 'active' : 'gray'" :label="a.is_variant ? $t('attributesPage.variant') : $t('attributesPage.info')" />
        </div>
        <div class="flex flex-wrap gap-2">
          <span v-for="v in valuesByAttr[a.id] || []" :key="v.id" class="chip border-slate-200 bg-lightbg text-ink">{{ v.label || v.value }}</span>
          <span v-if="!(valuesByAttr[a.id] || []).length" class="text-sm text-muted">{{ $t('attributesPage.noValues') }}</span>
        </div>
        <button v-if="tenant.canWrite" class="btn btn-outline btn-sm mt-4" @click="openVal(a)"><Plus class="h-4 w-4" /> {{ $t('attributesPage.addValue') }}</button>
      </div>
    </div>

    <EmptyState v-else :icon="Tag" :title="$t('attributesPage.emptyTitle')" :message="$t('attributesPage.emptyMessage')">
      <button v-if="tenant.canWrite" class="btn btn-primary btn-sm" @click="attrModal = true">{{ $t('attributesPage.addAttribute') }}</button>
    </EmptyState>

    <!-- Attribute modal -->
    <Modal v-model="attrModal" :title="$t('attributesPage.newAttribute')">
      <form id="attr-form" class="grid gap-4" @submit.prevent="createAttr">
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="attrForm.name" :label="$t('common.name')" placeholder="Color" required />
          <FormField v-model="attrForm.code" :label="$t('attributesPage.code')" placeholder="color" />
        </div>
        <FormField v-model.number="attrForm.sort_order" :label="$t('attributesPage.sortOrder')" type="number" />
        <label class="flex items-center gap-2 text-sm"><input v-model="attrForm.is_variant" type="checkbox" class="rounded border-slate-300 text-primary-600 focus:ring-primary-500" /> {{ $t('attributesPage.variantAttribute') }}</label>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="attrModal = false">{{ $t('common.cancel') }}</button>
          <button form="attr-form" type="submit" class="btn btn-primary" :disabled="attrBusy"><Spinner v-if="attrBusy" :size="18" /><span v-else>{{ $t('common.create') }}</span></button>
        </div>
      </template>
    </Modal>

    <!-- Value modal -->
    <Modal v-model="valModal" :title="valAttr ? $t('attributesPage.addValueFor', { name: valAttr.name }) : $t('attributesPage.addValue')">
      <form id="val-form" class="grid gap-4" @submit.prevent="createVal">
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="valForm.value" :label="$t('attributesPage.value')" placeholder="red" required />
          <FormField v-model="valForm.label" :label="$t('attributesPage.label')" placeholder="Red" />
        </div>
        <FormField v-model.number="valForm.sort_order" :label="$t('attributesPage.sortOrder')" type="number" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="valModal = false">{{ $t('common.cancel') }}</button>
          <button form="val-form" type="submit" class="btn btn-primary" :disabled="valBusy"><Spinner v-if="valBusy" :size="18" /><span v-else>{{ $t('attributesPage.addValue') }}</span></button>
        </div>
      </template>
    </Modal>
  </div>
</template>
