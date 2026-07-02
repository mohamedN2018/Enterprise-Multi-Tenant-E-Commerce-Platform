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
  locale.value = l === 'en' ? 'en' : 'ar';
  localStorage.setItem('locale', locale.value);
  applyDir();
}

export function useI18n() {
  return { t, locale, dir, setLocale };
}
