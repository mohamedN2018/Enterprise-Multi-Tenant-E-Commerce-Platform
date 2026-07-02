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
const form = ref({ name: '', currency: 'USD', country: '', description: '' });

const createStore = async () => {
  creating.value = true;
  try {
    const res = await seller.createStore(form.value);
    ui.success('Store created!');
    showCreate.value = false;
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
    <div v-if="!ready" class="flex min-h-[50vh] items-center justify-center"><Spinner :size="30" label="Loading…" /></div>

    <!-- No store yet: onboarding -->
    <div v-else-if="!tenant.hasStores && !tenant.isPlatform">
      <PageHeader title="Welcome to your Seller Center" subtitle="Create your first store to start selling." />
      <EmptyState :icon="StoreIcon" title="You don't have a store yet" message="Open a store to add products, manage orders and grow your business.">
        <button class="btn btn-primary" @click="showCreate = true"><Plus class="h-4 w-4" /> Create store</button>
      </EmptyState>
    </div>

    <!-- Role-specific dashboard -->
    <component :is="dashboardComponent" v-else />

    <!-- Create store modal -->
    <Modal v-model="showCreate" title="Create a new store">
      <form id="create-store" class="grid gap-4" @submit.prevent="createStore">
        <FormField v-model="form.name" label="Store name" placeholder="Acme Supplies" required />
        <div class="grid grid-cols-2 gap-4">
          <FormField v-model="form.currency" label="Currency" placeholder="USD" maxlength="3" />
          <FormField v-model="form.country" label="Country (ISO-2)" placeholder="US" maxlength="2" />
        </div>
        <FormField v-model="form.description" label="Description" placeholder="What do you sell?" />
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showCreate = false">Cancel</button>
          <button form="create-store" type="submit" class="btn btn-primary" :disabled="creating">
            <Spinner v-if="creating" :size="18" /><span v-else>Create store</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
