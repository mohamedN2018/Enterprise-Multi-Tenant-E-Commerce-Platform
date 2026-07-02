<script setup>
import { ref, computed, onMounted } from 'vue';
import { Store as StoreIcon, Plus } from 'lucide-vue-next';
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

const tenant = useTenantStore();
const ui = useUiStore();

const ready = ref(false);

// Each role gets a distinct dashboard experience.
const dashboardComponent = computed(() => {
  if (tenant.isPlatform) return PlatformDashboard;
  if (tenant.role === 'employee') return StaffDashboard;
  return SellerDashboard;
});

const showCreate = ref(false);
const creating = ref(false);
const form = ref({ name: '', currency: 'USD', country: '', description: '', owner_email: '' });

const createStore = async () => {
  creating.value = true;
  try {
    const { owner_email, ...storePayload } = form.value;
    const res = await seller.createStore(storePayload);
    // Platform provisioning: optionally hand the store to a seller as owner.
    if (owner_email && owner_email.trim()) {
      try {
        await seller.addMember(res.data.id, { user_email: owner_email.trim(), role: 'owner' });
      } catch (e) {
        ui.error(errorMessage(e));
      }
    }
    ui.success(t('admin.storeCreated'));
    showCreate.value = false;
    form.value = { name: '', currency: 'USD', country: '', description: '', owner_email: '' };
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
      <!-- Platform admin: provision a store for a seller -->
      <template v-if="tenant.isPlatform">
        <PageHeader :title="$t('admin.provisionStore')" :subtitle="$t('admin.provisionSubtitle')" />
        <EmptyState :icon="StoreIcon" :title="$t('admin.noStores')" :message="$t('admin.provisionSubtitle')">
          <button class="btn btn-primary" @click="showCreate = true"><Plus class="h-4 w-4" /> {{ $t('admin.provisionStore') }}</button>
        </EmptyState>
      </template>
      <!-- Seller with no store: no self-registration; contact admin -->
      <template v-else>
        <PageHeader :title="$t('admin.welcomeSeller')" />
        <EmptyState :icon="StoreIcon" :title="$t('admin.contactAdminTitle')" :message="$t('admin.contactAdminMsg')" />
      </template>
    </div>

    <!-- Role-specific dashboard -->
    <component :is="dashboardComponent" v-else />

    <!-- Provision store modal (platform admin only) -->
    <Modal v-model="showCreate" :title="$t('admin.createNewStore')">
      <form id="create-store" class="grid gap-4" @submit.prevent="createStore">
        <FormField v-model="form.name" :label="$t('admin.storeName')" placeholder="Acme Supplies" required />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="form.currency" :label="$t('admin.currency')" placeholder="USD" maxlength="3" />
          <FormField v-model="form.country" :label="$t('admin.countryIso')" placeholder="US" maxlength="2" />
        </div>
        <FormField v-model="form.description" :label="$t('common.description')" :placeholder="$t('admin.whatSell')" />
        <FormField v-model="form.owner_email" :label="$t('admin.assignOwnerEmail')" type="email" placeholder="seller@example.com" :hint="$t('admin.assignOwnerHint')" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showCreate = false">{{ $t('common.cancel') }}</button>
          <button form="create-store" type="submit" class="btn btn-primary" :disabled="creating">
            <Spinner v-if="creating" :size="18" /><span v-else>{{ $t('admin.createStore') }}</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
