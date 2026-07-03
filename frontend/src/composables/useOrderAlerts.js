import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import { useTenantStore } from '@/stores/tenant';
import { useUiStore } from '@/stores/ui';
import { seller } from '@/services/seller';
import { t } from '@/i18n';

// Poll the store's orders and alert the seller (sound + toast) the moment a new
// one lands — so an owner "hears" incoming orders without watching the screen.
// Consumes only the existing /orders/manage/ endpoint (no backend changes).

const POLL_MS = 30000;
const MUTE_KEY = 'q_order_sound_muted';
const seenKey = (storeId) => `q_last_order_${storeId}`;

const readMute = () => {
  try {
    return localStorage.getItem(MUTE_KEY) === '1';
  } catch {
    return false;
  }
};

// Shared reactive mute flag, so a toggle anywhere stays in sync.
export const orderSoundMuted = ref(readMute());

export function toggleOrderSound() {
  orderSoundMuted.value = !orderSoundMuted.value;
  try {
    localStorage.setItem(MUTE_KEY, orderSoundMuted.value ? '1' : '0');
  } catch {
    /* ignore */
  }
}

// Two-tone "cash register" chime via Web Audio — no asset, respects the mute
// flag, and silently no-ops if the browser blocks audio before a user gesture.
function playChime() {
  if (orderSoundMuted.value) return;
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = new AC();
    const now = ctx.currentTime;
    const tone = (freq, start, dur) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'sine';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.0001, now + start);
      gain.gain.exponentialRampToValueAtTime(0.22, now + start + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur);
      osc.start(now + start);
      osc.stop(now + start + dur + 0.02);
    };
    tone(880, 0, 0.18);
    tone(1320, 0.16, 0.3);
    setTimeout(() => {
      try {
        ctx.close();
      } catch {
        /* ignore */
      }
    }, 800);
  } catch {
    /* ignore */
  }
}

export function useOrderAlerts() {
  const tenant = useTenantStore();
  const ui = useUiStore();
  let timer = null;
  let baseline = null; // newest acknowledged order id (string) for the active store
  let baselineStore = null;

  const readSeen = (sid) => {
    try {
      return localStorage.getItem(seenKey(sid));
    } catch {
      return null;
    }
  };
  const writeSeen = (sid, id) => {
    try {
      localStorage.setItem(seenKey(sid), String(id));
    } catch {
      /* ignore */
    }
  };

  const poll = async () => {
    const sid = tenant.activeId;
    if (!sid) return;
    // Reset the baseline whenever the active store changes.
    if (baselineStore !== sid) {
      baselineStore = sid;
      baseline = readSeen(sid);
    }
    try {
      const res = await seller.orders({ page_size: 5, ordering: '-created_at' });
      const list = res.data?.results || res.data || [];
      if (!list.length) return;
      const newest = list[0];
      const newestId = String(newest.id);
      // First sighting for this store → remember it, don't alert on backlog.
      if (baseline == null) {
        baseline = newestId;
        writeSeen(sid, newestId);
        return;
      }
      if (newestId === baseline) return;
      // How many of the newest orders are ahead of the baseline? (exact when the
      // baseline is still within the page, otherwise report the whole page.)
      const idx = list.findIndex((o) => String(o.id) === baseline);
      const count = idx === -1 ? list.length : idx || 1;
      playChime();
      ui.info(
        count === 1
          ? t('orderAlerts.newOrder', { n: newest.number || newestId })
          : t('orderAlerts.newOrders', { n: count })
      );
      baseline = newestId;
      writeSeen(sid, newestId);
    } catch {
      /* transient — try again next tick */
    }
  };

  // Poll as soon as a store becomes active (ensureReady resolves async, so the
  // active id may not be set yet at mount), and again on every store switch.
  watch(
    () => tenant.activeId,
    (sid) => {
      if (sid) poll();
    },
    { immediate: true }
  );
  onMounted(() => {
    timer = setInterval(poll, POLL_MS);
  });
  onBeforeUnmount(() => timer && clearInterval(timer));
}
