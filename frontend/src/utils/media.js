// Product/store imagery. Only REAL uploaded images are shown; when there is
// none we render a clean, neutral local placeholder (no external/stock photos),
// so what you see is always the seller's own image.

// A neutral "no image yet" placeholder (inline SVG — no network request).
const neutralSvg = (w, h) =>
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">` +
      `<rect width="${w}" height="${h}" fill="#eef2f7"/>` +
      `<g transform="translate(${w / 2} ${h / 2})" fill="#c3cddb">` +
      `<circle cx="${-w * 0.09}" cy="${-h * 0.07}" r="${Math.max(6, h * 0.06)}"/>` +
      `<path d="M${-w * 0.2} ${h * 0.16} L${-w * 0.05} ${-h * 0.05} L${w * 0.03} ${h * 0.09} L${w * 0.12} ${-h * 0.02} L${w * 0.2} ${h * 0.16} Z"/>` +
      `</g></svg>`
  );

const FALLBACK = neutralSvg(8, 6);

// First real image from a product: the cover (`image`) or the first gallery item.
const realProductImage = (p) => p?.image || p?.images?.[0]?.image || p?.images?.[0] || '';

export const productImage = (p, w = 600, h = 450) => realProductImage(p) || neutralSvg(w, h);

export const catImage = (_name, s = 400) => neutralSvg(s, s);

export const storeBanner = (store, w = 1200, h = 320) => store?.banner || neutralSvg(w, h);

export const storeLogo = (store, size = 96) => store?.logo || neutralSvg(size, size);

export const heroImage = (_key = 'hero', w = 1600, h = 520) => neutralSvg(w, h);

export const onImgError = (e) => {
  const el = e.target;
  if (el.dataset.fb) return;
  el.dataset.fb = '1';
  el.src = FALLBACK;
};

export const money = (v, currency = '') => (v == null ? '—' : `${v} ${currency}`.trim());
