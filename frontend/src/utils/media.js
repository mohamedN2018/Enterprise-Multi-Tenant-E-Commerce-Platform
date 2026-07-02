// Deterministic placeholder imagery (seeded picsum) with a neutral fallback.
const FALLBACK =
  'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="8" height="6"><rect width="8" height="6" fill="%23e2e8f0"/></svg>';

const seed = (v) => encodeURIComponent(String(v ?? 'x'));

export const productImage = (p, w = 600, h = 450) =>
  `https://picsum.photos/seed/${seed(p?.slug || p?.id || p?.name)}-p/${w}/${h}`;

export const storeBanner = (s, w = 1200, h = 320) =>
  s?.banner || `https://picsum.photos/seed/${seed(s?.slug || s?.name)}-banner/${w}/${h}`;

export const storeLogo = (s, size = 96) =>
  s?.logo || `https://picsum.photos/seed/${seed(s?.slug || s?.name)}-logo/${size}/${size}`;

export const heroImage = (key = 'hero', w = 1600, h = 520) =>
  `https://picsum.photos/seed/marketplace-${key}/${w}/${h}`;

export const catImage = (name, s = 400) => `https://picsum.photos/seed/${seed(name)}-cat/${s}/${s}`;

export const onImgError = (e) => {
  const el = e.target;
  if (el.dataset.fb) return;
  el.dataset.fb = '1';
  el.src = FALLBACK;
};

export const money = (v, currency = '') => (v == null ? '—' : `${v} ${currency}`.trim());
