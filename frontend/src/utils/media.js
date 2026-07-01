// Image helpers for the storefront. Real images (store logo/banner) are used
// when the API provides them; otherwise we fall back to deterministic external
// placeholders (picsum, seeded so each entity keeps the same image), with a
// bundled template image as the final offline fallback.

import p1 from 'assets/images/widget/p1.png';
import p2 from 'assets/images/widget/p2.png';
import p3 from 'assets/images/widget/p3.png';
import p4 from 'assets/images/widget/p4.png';

const LOCAL = [p1, p2, p3, p4];

const hash = (str) => {
  let h = 0;
  const s = String(str || '');
  for (let i = 0; i < s.length; i += 1) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
};

const seed = (obj, suffix = '') => encodeURIComponent(`${obj?.slug || obj?.id || obj?.name || 'x'}${suffix}`);

// Local template image, chosen deterministically — used as onError fallback.
export const localImage = (key) => LOCAL[hash(key) % LOCAL.length];

export const productImage = (p, w = 600, h = 450) => `https://picsum.photos/seed/${seed(p, '-p')}/${w}/${h}`;

export const storeBanner = (s, w = 1600, h = 400) => s?.banner || `https://picsum.photos/seed/${seed(s, '-banner')}/${w}/${h}`;

export const storeLogo = (s, size = 160) => s?.logo || `https://picsum.photos/seed/${seed(s, '-logo')}/${size}/${size}`;

export const heroImage = (w = 1600, h = 500) => `https://picsum.photos/seed/marketplace-hero/${w}/${h}`;

// Attach to an <img onError> to swap in a bundled fallback once.
export const onImgError = (key) => (e) => {
  if (e.currentTarget.dataset.fallback) return;
  e.currentTarget.dataset.fallback = '1';
  e.currentTarget.src = localImage(key);
};
