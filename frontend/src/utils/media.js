// Real-looking product imagery via keyword photo service, stable per product.
const FALLBACK =
  'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="8" height="6"><rect width="8" height="6" fill="%23e2e8f0"/></svg>';

const hash = (v) => {
  let h = 0;
  const s = String(v ?? 'x');
  for (let i = 0; i < s.length; i += 1) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
};

// A curated set of e-commerce keywords so every product shows a real product photo.
const PRODUCT_KEYWORDS = [
  'headphones', 'wristwatch', 'sneakers', 'laptop', 'camera', 'sunglasses',
  'backpack', 'smartphone', 'perfume', 'handbag', 'keyboard', 'coffee-mug',
  'chair', 'desk-lamp', 'tshirt', 'shoes', 'watch', 'bluetooth-speaker',
  'tablet', 'jacket', 'cosmetics', 'drone', 'game-controller', 'wallet'
];

const flickr = (kw, w, h, seed) =>
  `https://loremflickr.com/${w}/${h}/${encodeURIComponent(kw)}?lock=${hash(seed) % 1000}`;

export const productImage = (p, w = 600, h = 450) => {
  const seed = p?.slug || p?.id || p?.name || 'x';
  const kw = PRODUCT_KEYWORDS[hash(seed) % PRODUCT_KEYWORDS.length];
  return flickr(kw, w, h, seed);
};

export const catImage = (name, s = 400) => flickr(`${name},product`, s, s, name);

export const storeBanner = (store, w = 1200, h = 320) =>
  store?.banner || flickr('shop,store,retail', w, h, store?.slug || store?.name || 'store');

export const storeLogo = (store, size = 96) =>
  store?.logo || `https://picsum.photos/seed/${encodeURIComponent(store?.slug || store?.name || 'x')}-logo/${size}/${size}`;

export const heroImage = (key = 'hero', w = 1600, h = 520) =>
  flickr('shopping,ecommerce,products', w, h, `hero-${key}`);

export const onImgError = (e) => {
  const el = e.target;
  if (el.dataset.fb) return;
  el.dataset.fb = '1';
  el.src = FALLBACK;
};

export const money = (v, currency = '') => (v == null ? '—' : `${v} ${currency}`.trim());
