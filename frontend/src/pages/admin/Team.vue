<script setup>
import { ref, computed, onMounted } from 'vue';
import { UserPlus, Trash2, Users, Pencil } from 'lucide-vue-next';
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
import { t } from '@/i18n';
import { useValidation, email } from '@/utils/validators';

const tenant = useTenantStore();
const ui = useUiStore();

const roles = ['manager', 'employee'];
const loading = ref(true);
const members = ref([]);
const storeId = ref(null);
const settings = ref(null);

const columns = computed(() => [
  { key: 'user_email', label: t('team.member'), sortable: true },
  { key: 'role', label: t('team.role'), sortable: true },
  { key: 'is_active', label: t('team.status'), sortable: true },
  { key: 'created_at', label: t('team.joined'), sortable: true },
  { key: 'actions', label: '', align: 'right' }
]);

// Employee limit lives in store settings.metadata (admin-set per agreement).
const maxEmployees = computed(() => {
  const v = settings.value?.metadata?.max_employees;
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : null;
});
const employeeCount = computed(() => members.value.filter((m) => m.role === 'employee').length);
const limitReached = computed(() => maxEmployees.value != null && employeeCount.value >= maxEmployees.value);

const load = async () => {
  loading.value = true;
  try {
    storeId.value = await tenant.ensureReady();
    if (!storeId.value) return;
    const res = await seller.members(storeId.value);
    members.value = res.data?.results || res.data || [];
    try {
      const s = await seller.storeSettings(storeId.value);
      settings.value = s.data || null;
    } catch {
      settings.value = null;
    }
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    loading.value = false;
  }
};

const showInvite = ref(false);
const inviting = ref(false);
const form = ref({ email: '', role: 'employee' });
const { errors, run, clear } = useValidation(() => form.value, { email: [email()] });

// Block adding an employee past the agreed cap (client-side guard).
const inviteBlocked = computed(() => form.value.role === 'employee' && limitReached.value);

const invite = async () => {
  if (inviteBlocked.value || !run()) return;
  inviting.value = true;
  try {
    await seller.addMember(storeId.value, form.value);
    ui.success(t('team.memberAdded'));
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
    ui.success(t('team.roleUpdated'));
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
    ui.success(t('team.memberRemoved'));
    confirmRemove.value = null;
    load();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    removing.value = false;
  }
};

// Platform admin sets the agreed employee cap.
const showLimit = ref(false);
const savingLimit = ref(false);
const limitForm = ref(0);
const openLimit = () => {
  limitForm.value = maxEmployees.value || 0;
  showLimit.value = true;
};
const saveLimit = async () => {
  savingLimit.value = true;
  try {
    const metadata = { ...(settings.value?.metadata || {}) };
    const n = Number(limitForm.value);
    if (Number.isFinite(n) && n > 0) metadata.max_employees = n;
    else delete metadata.max_employees;
    const res = await seller.updateStoreSettings(storeId.value, { metadata });
    settings.value = res.data || { ...settings.value, metadata };
    ui.success(t('team.limitSaved'));
    showLimit.value = false;
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    savingLimit.value = false;
  }
};

onMounted(load);
</script>

<template>
  <div>
    <PageHeader :title="$t('team.title')" :subtitle="$t('team.subtitle')">
      <template #actions>
        <span class="chip border-slate-200 bg-slate-100 text-slate-600">
          <Users class="h-3.5 w-3.5" /> {{ $t('team.employees') }}: {{ employeeCount }}<template v-if="maxEmployees != null"> / {{ maxEmployees }}</template>
        </span>
        <button v-if="tenant.isPlatform" class="btn btn-ghost btn-sm" @click="openLimit"><Pencil class="h-4 w-4" /> {{ $t('team.editLimit') }}</button>
        <span v-if="!tenant.canAdminTeam" class="chip border-slate-200 bg-slate-100 text-slate-600">{{ $t('team.ownersManageRoles') }}</span>
        <button v-if="tenant.canManageMembers" class="btn btn-primary btn-sm" :disabled="!tenant.hasStores" @click="showInvite = true">
          <UserPlus class="h-4 w-4" /> {{ $t('team.addMember') }}
        </button>
      </template>
    </PageHeader>

    <div v-if="limitReached && tenant.canManageMembers" class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      {{ $t('team.limitReachedMsg', { max: maxEmployees }) }}
    </div>

    <DataTable :columns="columns" :rows="members" :loading="loading" :empty-title="$t('team.noMembers')" :empty-message="$t('team.noMembersMsg')">
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
          v-if="tenant.canAdminTeam && row.role !== 'owner'"
          :value="row.role"
          class="input h-9 max-w-[140px] py-1 text-sm capitalize"
          @change="changeRole(row, $event.target.value)"
        >
          <option v-for="r in roles" :key="r" :value="r">{{ $t('roles.' + r) }}</option>
        </select>
        <StatusBadge v-else :status="row.role === 'owner' ? 'indigo' : 'gray'" :label="$t('roles.' + row.role)" />
      </template>
      <template #cell-is_active="{ value }"><StatusBadge :status="value ? 'active' : 'inactive'" /></template>
      <template #cell-created_at="{ value }">{{ (value || '').slice(0, 10) }}</template>
      <template #cell-actions="{ row }">
        <button v-if="tenant.canAdminTeam && row.role !== 'owner'" class="btn btn-ghost btn-sm text-rose-600" @click="confirmRemove = row">
          <Trash2 class="h-4 w-4" />
        </button>
      </template>
    </DataTable>

    <Modal v-model="showInvite" :title="$t('team.addTeamMember')">
      <form id="invite-form" class="grid gap-4" novalidate @submit.prevent="invite">
        <FormField v-model="form.email" :label="$t('team.emailAddress')" type="email" placeholder="teammate@example.com" :error="errors.email" @update:model-value="clear('email')" />
        <div>
          <label class="label">{{ $t('team.role') }}</label>
          <select v-model="form.role" class="input">
            <option v-for="r in roles" :key="r" :value="r">{{ $t('roles.' + r) }}</option>
          </select>
        </div>
        <p v-if="inviteBlocked" class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          {{ $t('team.limitReachedMsg', { max: maxEmployees }) }}
        </p>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showInvite = false">{{ $t('common.cancel') }}</button>
          <button form="invite-form" type="submit" class="btn btn-primary" :disabled="inviting || inviteBlocked">
            <Spinner v-if="inviting" :size="18" /><span v-else>{{ $t('team.addMember') }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <Modal :model-value="!!confirmRemove" :title="$t('team.removeMember')" size="sm" @update:model-value="confirmRemove = null">
      <p class="text-sm text-slate-600">{{ $t('team.removeConfirm', { email: confirmRemove?.user_email }) }}</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="confirmRemove = null">{{ $t('common.cancel') }}</button>
          <button class="btn btn-danger" :disabled="removing" @click="doRemove">
            <Spinner v-if="removing" :size="18" /><span v-else>{{ $t('team.remove') }}</span>
          </button>
        </div>
      </template>
    </Modal>

    <!-- Platform admin: set agreed employee cap -->
    <Modal v-model="showLimit" :title="$t('team.employeeLimit')" size="sm">
      <form id="limit-form" class="grid gap-3" @submit.prevent="saveLimit">
        <FormField v-model="limitForm" :label="$t('team.maxEmployees')" type="number" min="0" :hint="$t('team.setByAdmin')" />
        <p class="text-xs text-slate-400">{{ $t('team.employees') }}: {{ employeeCount }}</p>
      </form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn btn-ghost" @click="showLimit = false">{{ $t('common.cancel') }}</button>
          <button form="limit-form" type="submit" class="btn btn-primary" :disabled="savingLimit">
            <Spinner v-if="savingLimit" :size="18" /><span v-else>{{ $t('team.saveLimit') }}</span>
          </button>
        </div>
      </template>
    </Modal>
  </div>
</template>
