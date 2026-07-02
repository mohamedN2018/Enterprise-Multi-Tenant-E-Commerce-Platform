<script setup>
import { ref, onMounted } from 'vue';
import { Bell, CheckCheck } from 'lucide-vue-next';
import { useTenantStore } from '@/stores/tenant';
import { seller } from '@/services/seller';

const tenant = useTenantStore();

const open = ref(false);
const unread = ref(0);
const items = ref([]);
const loading = ref(false);

const loadUnread = async () => {
  if (!tenant.activeId) return;
  try {
    const res = await seller.notificationsUnread();
    unread.value = res.data?.unread || 0;
  } catch {
    unread.value = 0;
  }
};

const loadRecent = async () => {
  if (!tenant.activeId) return;
  loading.value = true;
  try {
    const res = await seller.notifications({ page_size: 6 });
    items.value = res.data?.results || res.data || [];
  } catch {
    items.value = [];
  } finally {
    loading.value = false;
  }
};

const toggle = () => {
  open.value = !open.value;
  if (open.value) loadRecent();
};

const markAll = async () => {
  try {
    await seller.markAllNotificationsRead();
    unread.value = 0;
    items.value = items.value.map((n) => ({ ...n, is_read: true }));
  } catch {
    /* ignore */
  }
};

onMounted(loadUnread);
</script>

<template>
  <div class="relative">
    <button class="relative grid h-10 w-10 place-items-center rounded-lg text-ink hover:bg-lightbg" @click="toggle" aria-label="Notifications">
      <Bell class="h-5 w-5" />
      <span v-if="unread" class="absolute -right-0.5 -top-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-secondary-500 px-1 text-[11px] font-bold text-white">
        {{ unread > 9 ? '9+' : unread }}
      </span>
    </button>

    <div v-if="open" class="fixed inset-0 z-30" @click="open = false"></div>
    <div v-if="open" class="absolute right-0 z-40 mt-2 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-pop">
      <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <p class="font-heading font-semibold text-ink">Notifications</p>
        <button v-if="unread" class="text-xs font-medium text-primary-600 hover:underline" @click="markAll"><CheckCheck class="mr-1 inline h-3.5 w-3.5" />Mark all read</button>
      </div>
      <div class="max-h-80 overflow-y-auto">
        <p v-if="loading" class="px-4 py-6 text-center text-sm text-muted">Loading…</p>
        <template v-else-if="items.length">
          <RouterLink
            v-for="n in items"
            :key="n.id"
            :to="{ name: 'admin-notifications' }"
            class="flex gap-3 border-b border-slate-50 px-4 py-3 transition last:border-0 hover:bg-lightbg"
            :class="n.is_read ? '' : 'bg-primary-50/40'"
            @click="open = false"
          >
            <span class="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full" :class="n.is_read ? 'bg-slate-100 text-slate-400' : 'bg-primary-100 text-primary-600'">
              <Bell class="h-4 w-4" />
            </span>
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-ink">{{ n.title || n.event_type }}</p>
              <p class="clamp-1 text-xs text-muted">{{ n.body }}</p>
            </div>
          </RouterLink>
        </template>
        <p v-else class="px-4 py-6 text-center text-sm text-muted">You're all caught up.</p>
      </div>
      <RouterLink :to="{ name: 'admin-notifications' }" class="block border-t border-slate-100 px-4 py-2.5 text-center text-sm font-medium text-primary-600 hover:bg-lightbg" @click="open = false">
        View all notifications
      </RouterLink>
    </div>
  </div>
</template>
