<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { Bell, CheckCheck } from 'lucide-vue-next';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { t } from '@/i18n';

const tenant = useTenantStore();
const ui = useUiStore();

const open = ref(false);
const unread = ref(0);
const items = ref([]);
const loading = ref(false);
let prevUnread = null;

// Short "ping" via the Web Audio API — no asset needed. Browsers only allow
// this after a user gesture; if blocked, it silently no-ops.
const playPing = () => {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = new AC();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.0001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.18, ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.35);
    osc.start();
    osc.stop(ctx.currentTime + 0.36);
    osc.onended = () => ctx.close();
  } catch {
    /* ignore */
  }
};

const loadUnread = async () => {
  if (!tenant.activeId) return;
  try {
    const res = await seller.notificationsUnread();
    const n = res.data?.unread || 0;
    // New notification arrived since the last poll → ping + toast.
    if (prevUnread !== null && n > prevUnread) {
      const delta = n - prevUnread;
      playPing();
      ui.info(delta === 1 ? t('notificationsPage.newNotification') : t('notificationsPage.newNotifications', { n: delta }));
    }
    prevUnread = n;
    unread.value = n;
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

let timer = null;
onMounted(() => {
  loadUnread();
  timer = setInterval(loadUnread, 60000);
});
onBeforeUnmount(() => timer && clearInterval(timer));
</script>

<template>
  <div class="relative">
    <button class="relative grid h-10 w-10 place-items-center rounded-lg text-ink hover:bg-lightbg" @click="toggle" :aria-label="$t('notificationsPage.title')">
      <Bell class="h-5 w-5" />
      <span v-if="unread" class="absolute -end-0.5 -top-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-secondary-500 px-1 text-[11px] font-bold text-white">
        {{ unread > 9 ? '9+' : unread }}
      </span>
    </button>

    <div v-if="open" class="fixed inset-0 z-[90]" @click="open = false"></div>
    <div v-if="open" class="absolute end-0 z-[100] mt-2 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-pop dark:border-slate-700 dark:bg-slate-800">
      <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <p class="font-heading font-semibold text-ink">{{ $t('notificationsPage.title') }}</p>
        <button v-if="unread" class="text-xs font-medium text-primary-600 hover:underline" @click="markAll"><CheckCheck class="me-1 inline h-3.5 w-3.5" />{{ $t('notificationsPage.markAllRead') }}</button>
      </div>
      <div class="max-h-80 overflow-y-auto">
        <p v-if="loading" class="px-4 py-6 text-center text-sm text-muted">{{ $t('common.loading') }}</p>
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
        <p v-else class="px-4 py-6 text-center text-sm text-muted">{{ $t('notificationsPage.allCaughtUp') }}</p>
      </div>
      <RouterLink :to="{ name: 'admin-notifications' }" class="block border-t border-slate-100 px-4 py-2.5 text-center text-sm font-medium text-primary-600 hover:bg-lightbg" @click="open = false">
        {{ $t('notificationsPage.viewAll') }}
      </RouterLink>
    </div>
  </div>
</template>
