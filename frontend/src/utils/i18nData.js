import { t } from '@/i18n';

// Localise DB-provided category names (a controlled vocabulary) through the
// `catmap` dictionary. Unknown names fall back to their raw value, and English
// mode (no catmap) shows the original name. Reactive: re-renders on locale change
// because it reads the i18n locale via t().
export const catLabel = (name) => {
  if (!name) return name;
  const key = `catmap.${name}`;
  const v = t(key);
  return v === key ? name : v;
};
