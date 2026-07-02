<script setup>
import { ref, onMounted } from 'vue';
import { Bell, Check, CheckCheck, Dot } from 'lucide-vue-next';
import PageHeader from '@/components/ui/PageHeader.vue';
import EmptyState from '@/components/ui/EmptyState.vue';
import Spinner from '@/components/ui/Spinner.vue';
import Pagination from '@/components/ui/Pagination.vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { usePaginated } from '@/composables/usePaginated';
import { seller } from '@/services/seller';
import { errorMessage } from '@/services/http';

const tenant = useTenantStore();
const ui = useUiStore();

const filter = ref('all'); // all | unread
const busy = ref(false);

const { items, page, total, totalPages, loading, load } = usePaginated((params) =>
  seller.notifications(params)
);

const fetch = () => load(filter.value === 'unread' ? { is_read: false } : {});
const changePage = (n) => {
  page.value = n;
  fetch();
};
const setFilter = (f) => {
  filter.value = f;
  page.value = 1;
  fetch();
};

const markRead = async (n) => {
  if (n.is_read) return;
  try {
    await seller.markNotificationRead(n.id);
    n.is_read = true;
  } catch (e) {
    ui.error(errorMessage(e));
  }
};

const markAll = async () => {
  busy.value = true;
  try {
    await seller.markAllNotificationsRead();
    ui.success('All marked read.');
    fetch();
  } catch (e) {
    ui.error(errorMessage(e));
  } finally {
    busy.value = false;
  }
};

onMounted(async () => {
  const id = await tenant.ensureReady();
  if (id) fetch();
});
</script>

<template>
  <div>
    <PageHeader title="Notifications" subtitle="Activity and alerts for your store.">
      <template #actions>
        <button class="btn btn-outline btn-sm" :disabled="busy" @click="markAll"><CheckCheck class="h-4 w-4" /> Mark all read</button>
      </template>
    </PageHeader>

    <div class="mb-4 flex gap-2">
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="filter === 'all' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="setFilter('all')">All</button>
      <button class="rounded-full px-4 py-1.5 text-sm font-medium transition" :class="filter === 'unread' ? 'bg-primary-600 text-white' : 'bg-lightbg text-ink hover:bg-primary-100'" @click="setFilter('unread')">Unread</button>
    </div>

    <div v-if="loading" class="flex min-h-[30vh] items-center justify-center"><Spinner :size="26" label="Loading…" /></div>

    <template v-else-if="items.length">
      <div class="card divide-y divide-slate-100 overflow-hidden p-0">
        <div
          v-for="n in items"
          :key="n.id"
          class="flex items-start gap-4 p-4 transition"
          :class="n.is_read ? '' : 'bg-primary-50/40'"
        >
          <span class="mt-0.5 grid h-10 w-10 shrink-0 place-items-center rounded-full" :class="n.is_read ? 'bg-slate-100 text-slate-400' : 'bg-primary-100 text-primary-600'">
            <Bell class="h-5 w-5" />
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <p class="font-heading font-semibold text-ink">{{ n.title || n.event_type }}</p>
              <Dot v-if="!n.is_read" class="h-5 w-5 text-primary-600" />
            </div>
            <p class="text-sm text-muted">{{ n.body }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ (n.created_at || '').replace('T', ' ').slice(0, 16) }}</p>
          </div>
          <button v-if="!n.is_read" class="btn btn-ghost btn-sm shrink-0" @click="markRead(n)"><Check class="h-4 w-4" /> Read</button>
        </div>
      </div>
      <div v-if="totalPages > 1" class="mt-6"><Pagination :page="page" :page-size="20" :total="total" @update:page="changePage" /></div>
    </template>

    <EmptyState v-else :icon="Bell" title="No notifications" message="You're all caught up." />
  </div>
</template>
