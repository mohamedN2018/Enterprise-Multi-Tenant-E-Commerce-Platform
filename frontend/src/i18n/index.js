import { ref, computed } from 'vue';
import messages from './messages';

// Arabic is the default/base locale; RTL follows automatically.
const stored = localStorage.getItem('locale');
export const locale = ref(stored === 'en' || stored === 'ar' ? stored : 'ar');
export const dir = computed(() => (locale.value === 'ar' ? 'rtl' : 'ltr'));

const lookup = (obj, path) => path.split('.').reduce((o, k) => (o == null ? o : o[k]), obj);

// Translate a dotted key; falls back to English then the raw key. Supports {param} interpolation.
export function t(key, params) {
  let msg = lookup(messages[locale.value], key);
  if (msg == null) msg = lookup(messages.en, key);
  if (msg == null) return key;
  if (params && typeof msg === 'string') {
    return msg.replace(/\{(\w+)\}/g, (_, k) => (params[k] != null ? params[k] : `{${k}}`));
  }
  return msg;
}

export function applyDir() {
  const el = document.documentElement;
  el.lang = locale.value;
  el.dir = dir.value;
}

export function setLocale(l) {
  const next = l === 'en' ? 'en' : 'ar';
  if (next === locale.value) return;
  locale.value = next;
  localStorage.setItem('locale', next);
  applyDir();
  // Product/store names & descriptions are localized server-side per request
  // (via the Accept-Language header), so already-fetched content stays in the
  // old language until it is re-fetched. Reload so the WHOLE app comes back in
  // the chosen language — not just the static UI, which switches reactively.
  if (typeof window !== 'undefined' && window.location) window.location.reload();
}

// Apply the platform's default language for a brand-new visitor only — an explicit
// user choice (stored) always wins. Persisted so it's stable (no header races).
export function initDefaultLocale(lang) {
  if (localStorage.getItem('locale')) return;
  const next = lang === 'en' ? 'en' : 'ar';
  locale.value = next;
  localStorage.setItem('locale', next);
  applyDir();
}

export function useI18n() {
  return { t, locale, dir, setLocale };
}
