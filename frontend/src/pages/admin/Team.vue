<script setup>
import { ref, onMounted } from 'vue';
import { UserPlus, Trash2 } from 'lucide-vue-next';
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

const roles = ['manager', 'employee'];
const loading = ref(true);
const members = ref([]);
const storeId = ref(null);

const columns = [
  { key: 'user_email', label: 'Member' },
  { key: 'role', label: 'Role' },
  { key: 'is_active', label: 'Status' },
  { key: 'created_at', label: 'Joined' },
  { key: 'actions', label: '', align: 'right' }
];

const load = async () => {
  loading.value = true;
  try {
    storeId.value = await tenant.ensureReady();
    if (!storeId.value) return;
    const res = await seller.members(storeId.value);
    members.value = res.data?.results || res.data || [];
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const showInvite = ref(false);
const inviting = ref(false);
const form = ref({ email: '', role: 'employee' });

const invite = async () => {
  inviting.value = true;
  try {
    await seller.addMember(storeId.value, form.value);
    ui.success('Member added.');
    showInvite.value = false;
    form.value = { email: '', role: 'employee' };
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    inviting.value = false;
  }
};

const changeRole = async (member, role) => {
  try {
    await seller.updateMember(storeId.value, member.id, { role });
    member.role = role;
    ui.success('Role updated.');
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

const confirmRemove = ref(null);
const removing = ref(false);
const doRemove = async () => {
  removing.value = true;
  try {
    await seller.removeMember(storeId.value, confirmRemove.value.id);
    ui.success('Member removed.');
    confirmRemove.value = null;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    removing.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <PageHeader title="Team" subtitle="Manage who can access this store.">
      <template #actions>
        <button class="btn btn-primary btn-sm" :disabled="!tenant.hasStores" @click="showInvite = true">
          <UserPlus class="h-4 w-4" /> Add member
        </button>
      </template>
    </PageHeader>

    <DataTable :columns="columns" :rows="members" :loading="loading" empty-title="No team members" empty-message="Invite people to help run your store.">
      <template #cell-user_email="{ row }">
        <div class="flex items-center gap-3">
          <span class="grid h-9 w-9 place-items-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
            {{ (row.user_email || '?').charAt(0).toUpperCase() }}
          </span>
          <span class="font-medium text-ink">{{ row.user_email }}</span>
        </div>
      </template>
      <template #cell-role="{ row }">
        <select
          v-if="row.role !== 'owner'"
          :value="row.role"
          class="input h-9 max-w-[140px] py-1 text-sm capitalize"
          @change="changeRole(row, $event.target.value)"
        >
          <option v-for="r in roles" :key="r" :value="r" class="capitalize">{{ r }}</option>
        </select>
        <StatusBadge v-else status="indigo" label="Owner" />
      </template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
      <template #cell-actions="{ row }">
        <button v-if="row.role !== 'owner'" class="btn btn-ghost btn-sm text-rose-600" @click="confirmRemove = row">
          <Trash2 class="h-4 w-4" />
        </button>
      </template>
    </DataTable>

    <Modal v-model="showInvite" title="Add team member">
      <form id="invite-form" class="grid gap-4" @submit.prevent="invite">
        <FormField v-model="form.email" label="Email address" type="email" placeholder="teammate@example.com" required />
        <div>
          <label class="label">Role</label>
          <select v-model="form.role" class="input capitalize">
            <option v-for="r in roles" :key="r" :value="r" class="capitalize">{{ r }}</option>
          </select>
        </div>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showInvite = false">Cancel</button>
          <button form="invite-form" type="submit" class="btn btn-primary" :disabled="inviting">
            <Spinner v-if="inviting" :size="18" /><span v-else>Add member</span>
          </button>
        </div>
      </template>
    </Modal>

    <Modal :model-value="!!confirmRemove" title="Remove member" size="sm" @update:model-value="confirmRemove = null">
      <p class="text-sm text-slate-600">Remove <span class="font-semibold">{{ confirmRemove?.user_email }}</span> from this store?</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="confirmRemove = null">Cancel</button>
          <button class="btn btn-danger" :disabled="removing" @click="doRemove">
            <Spinner v-if="removing" :size="18" /><span v-else>Remove</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
