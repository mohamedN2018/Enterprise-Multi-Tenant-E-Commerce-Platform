import { reactive } from 'vue';
import { t } from '@/i18n';

// Predicates
export const isEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(v ?? '').trim());
export const isUrl = (v) => /^https?:\/\/[^\s]+\.[^\s]+/i.test(String(v ?? '').trim());
export const isBlank = (v) => !String(v ?? '').trim();

// Rule builders — each returns a validator (value) => errorMessage | ''.
// Messages resolve through i18n at call time, so they follow the locale.
export const required = () => (v) => (isBlank(v) ? t('valid.required') : '');
export const email = () => (v) => (isBlank(v) ? t('valid.required') : isEmail(v) ? '' : t('valid.email'));
export const min = (n) => (v) => {
  if (isBlank(v)) return t('valid.required');
  return String(v).length >= n ? '' : t('valid.min', { n });
};
export const max = (n) => (v) => (String(v ?? '').length <= n ? '' : t('valid.max', { n }));
export const url = ({ optional = false } = {}) => (v) => {
  if (isBlank(v)) return optional ? '' : t('valid.required');
  return isUrl(v) ? '' : t('valid.url');
};
export const iso2 = ({ optional = false } = {}) => (v) => {
  if (isBlank(v)) return optional ? '' : t('valid.required');
  return /^[A-Za-z]{2}$/.test(String(v).trim()) ? '' : t('valid.iso2');
};
export const numberMin = (m = 0) => (v) => {
  const n = Number(v);
  if (!Number.isFinite(n)) return t('valid.number');
  return n >= m ? '' : t('valid.numberMin', { n: m });
};
export const positive = () => (v) => {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? '' : t('valid.positive');
};
export const sameAs = (getOther, msg) => (v) => (v === getOther() ? '' : msg || t('valid.match'));

// Run a { field: [rule, ...] } schema against a values object.
// Returns { errors, valid }. First failing rule per field wins.
export function validate(values, schema) {
  const errors = {};
  let valid = true;
  for (const field of Object.keys(schema)) {
    const rules = schema[field];
    for (const rule of rules) {
      const msg = rule(values[field]);
      if (msg) {
        errors[field] = msg;
        valid = false;
        break;
      }
    }
  }
  return { errors, valid };
}

// Small helper: a reactive errors bag + a validate() bound to a schema getter.
export function useValidation(getValues, schema) {
  const errors = reactive({});
  const run = () => {
    const res = validate(getValues(), typeof schema === 'function' ? schema() : schema);
    Object.keys(errors).forEach((k) => delete errors[k]);
    Object.assign(errors, res.errors);
    return res.valid;
  };
  const clear = (field) => {
    if (field) delete errors[field];
    else Object.keys(errors).forEach((k) => delete errors[k]);
  };
  return { errors, run, clear };
}
