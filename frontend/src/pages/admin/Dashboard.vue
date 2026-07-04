<script setup>
import { ref, computed, onMounted } from 'vue';
import { Store as StoreIcon, Plus, Globe } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import PageHeader from '@/components/ui/PageHeader.vue';
import Spinner from '@/components/ui/Spinner.vue';
import Modal from '@/components/ui/Modal.vue';
import FormField from '@/components/ui/FormField.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import SellerDashboard from './dashboards/SellerDashboard.vue';
import StaffDashboard from './dashboards/StaffDashboard.vue';
import PlatformDashboard from './dashboards/PlatformDashboard.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';
import { t } from '@/i18n';
import { useValidation, required, iso2 } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();
const router = useRouter();

const ready = ref(false);

// Each role gets a distinct dashboard experience. The super admin sees the
// platform oversight until they pick a store — then they see that store's
// dashboard, exactly as its owner would.
const dashboardComponent = computed(() => {
  if (tenant.isPlatform && !tenant.activeId) return PlatformDashboard;
  if (tenant.role === 'employee') return StaffDashboard;
  return SellerDashboard;
});

// Contracted sellers open their own store (they become its owner). The super
// admin does not create stores — they only oversee.
const showCreate = ref(false);
const creating = ref(false);
const form = ref({ name: '', currency: 'USD', country: '', description: '' });
const { errors, run, clear } = useValidation(
  () => form.value,
  { name: [required()], country: [iso2({ optional: true })] }
);

const createStore = async () => {
  if (!run()) return;
  creating.value = true;
  try {
    const res = await seller.createStore(form.value);
    ui.success(t('admin.storeCreated'));
    showCreate.value = false;
    form.value = { name: '', currency: 'USD', country: '', description: '' };
    await tenant.refresh();
    tenant.select(res.data.id);
    await tenant.resolveRole();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    creating.value = false;
  }
};

onMounted(async () => {
  await tenant.ensureReady();
  ready.value = true;
});
</script>

<template>
  <div>
    <div v-if="!ready" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" :label="$t('admin.loading')" /></div>

    <!-- No store yet -->
    <div v-else-if="!tenant.hasStores">
      <!-- Super admin: oversight only — cannot create stores -->
      <template v-if="tenant.isPlatform">
        <PageHeader :title="$t('admin.overseeTitle')" :subtitle="$t('admin.platform')" />
        <EmptyState :icon="Globe" :title="$t('admin.overseeTitle')" :message="$t('admin.overseeMsg')">
          <button class="btn btn-primary" @click="router.push({ name: 'admin-platform' })"><Globe class="h-4 w-4" /> {{ $t('admin.goToPlatform') }}</button>
        </EmptyState>
      </template>
      <!-- Contracted seller: open your own store -->
      <template v-else>
        <PageHeader :title="$t('admin.welcomeSeller')" :subtitle="$t('admin.welcomeSellerSub')" />
        <EmptyState :icon="StoreIcon" :title="$t('admin.noStoreYet')" :message="$t('admin.noStoreYetMsg')">
          <button class="btn btn-primary" @click="showCreate = true"><Plus class="h-4 w-4" /> {{ $t('admin.openStore') }}</button>
        </EmptyState>
      </template>
    </div>

    <!-- Role-specific dashboard -->
    <component :is="dashboardComponent" v-else />

    <!-- Open store modal (contracted sellers) -->
    <Modal v-model="showCreate" :title="$t('admin.openStore')">
      <form id="create-store" class="grid gap-4" novalidate @submit.prevent="createStore">
        <FormField v-model="form.name" :label="$t('admin.storeName')" placeholder="Acme Supplies" :error="errors.name" @update:model-value="clear('name')" />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="form.currency" :label="$t('admin.currency')" placeholder="USD" maxlength="3" />
          <FormField v-model="form.country" :label="$t('admin.countryIso')" placeholder="US" maxlength="2" :error="errors.country" @update:model-value="clear('country')" />
        </div>
        <FormField v-model="form.description" :label="$t('common.description')" :placeholder="$t('admin.whatSell')" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showCreate = false">{{ $t('common.cancel') }}</button>
          <button form="create-store" type="submit" class="btn btn-primary" :disabled="creating">
            <Spinner v-if="creating" :size="18" /><span v-else>{{ $t('admin.openStore') }}</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
