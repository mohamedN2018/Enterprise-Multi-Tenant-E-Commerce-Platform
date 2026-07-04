import { locale } from '@/i18n';

// Display label for a marketplace category. The category's canonical `name`
// (Arabic) is the filter key; `name_en` is shown when the visitor picks English.
// Reactive: re-reads the i18n locale so it re-renders on language switch.
export const catName = (cat) => {
  if (!cat) return '';
  return locale.value === 'en' && cat.name_en ? cat.name_en : cat.name || '';
};
