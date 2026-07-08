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

// Branded default product image (static, same-origin) — reliable everywhere and
// nicer than a bare grey box. Shown whenever a product has no real image.
const PRODUCT_FALLBACK = '/brand/product-placeholder.svg';

// First real image from a product: the cover (`image`) or the first gallery item.
const realProductImage = (p) => p?.image || p?.images?.[0]?.image || p?.images?.[0] || '';

export const productImage = (p) => realProductImage(p) || PRODUCT_FALLBACK;

// Categories carry no uploaded image, so we render a distinct, deterministic
// tile per category: a brand-coordinated gradient keyed on the name plus its
// initial. Same name → same colour every time; different names look varied but
// belong to one set (no repetitive grey boxes).
const escapeXml = (s) =>
  s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

// Warm + jewel tones that sit next to the orange/red brand palette.
const CAT_HUES = [28, 8, 42, 174, 239, 347, 158, 262, 199, 96];

export const catImage = (name = '', s = 400) => {
  const label = String(name || '').trim();
  let n = 0;
  for (let i = 0; i < label.length; i += 1) n = (n + label.charCodeAt(i)) % 9973;
  const hue = CAT_HUES[n % CAT_HUES.length];
  const initial = escapeXml(label ? Array.from(label)[0].toUpperCase() : '★');
  return (
    'data:image/svg+xml;utf8,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="${s}" height="${s}" viewBox="0 0 ${s} ${s}">` +
        `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
        `<stop offset="0" stop-color="hsl(${hue} 68% 52%)"/>` +
        `<stop offset="1" stop-color="hsl(${(hue + 18) % 360} 70% 38%)"/>` +
        `</linearGradient></defs>` +
        `<rect width="${s}" height="${s}" fill="url(#g)"/>` +
        `<text x="50%" y="52%" text-anchor="middle" dominant-baseline="central" ` +
        `font-family="Cairo, 'Segoe UI', Arial, sans-serif" font-size="${s * 0.42}" ` +
        `font-weight="800" fill="rgba(255,255,255,0.92)">${initial}</text>` +
        `</svg>`
    )
  );
};

export const storeBanner = (store, w = 1200, h = 320) => store?.banner || neutralSvg(w, h);

export const storeLogo = (store, size = 96) => store?.logo || neutralSvg(size, size);

export const heroImage = (_key = 'hero', w = 1600, h = 520) => neutralSvg(w, h);

export const onImgError = (e) => {
  const el = e.target;
  if (el.dataset.fb) return;
  el.dataset.fb = '1';
  el.src = PRODUCT_FALLBACK;
};

export const money = (v, currency = '') => (v == null ? '—' : `${v} ${currency}`.trim());
