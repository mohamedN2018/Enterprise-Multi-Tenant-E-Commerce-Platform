import { ref } from 'vue';

// Light is the default theme; persisted per user in localStorage.
const stored = localStorage.getItem('theme');
export const theme = ref(stored === 'dark' ? 'dark' : 'light');

export function applyTheme() {
  document.documentElement.classList.toggle('dark', theme.value === 'dark');
}

export function setTheme(t) {
  theme.value = t === 'dark' ? 'dark' : 'light';
  localStorage.setItem('theme', theme.value);
  applyTheme();
}

export function toggleTheme() {
  setTheme(theme.value === 'dark' ? 'light' : 'dark');
}

export function useTheme() {
  return { theme, setTheme, toggleTheme };
}

// --- Brand theme (platform-admin controlled colors + font) -----------------

// The live brand config the admin page binds to.
export const brand = ref(null);

const hexToRgb = (hex) => {
  const h = String(hex || '').replace('#', '');
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
};
const triplet = (hex) => hexToRgb(hex).join(' ');

const rgbToHsl = (r, g, b) => {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h /= 6;
  }
  return [h, s, l];
};
const hslTriplet = (h, s, l) => {
  let r, g, b;
  if (s === 0) { r = g = b = l; }
  else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3); g = hue2rgb(p, q, h); b = hue2rgb(p, q, h - 1 / 3);
  }
  return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)].join(' ');
};

// Per-shade lightness; 600 keeps the picked color's own lightness.
const SHADE_L = { 50: 0.96, 100: 0.9, 200: 0.8, 300: 0.68, 400: 0.58, 500: 0.52, 600: null, 700: 0.39, 800: 0.31, 900: 0.24 };
const scaleFrom = (hex) => {
  const [h, s, baseL] = rgbToHsl(...hexToRgb(hex));
  const out = {};
  for (const [shade, L] of Object.entries(SHADE_L)) out[shade] = hslTriplet(h, s, L === null ? baseL : L);
  return out;
};

export function applyBrand(config) {
  if (!config) return;
  const root = document.documentElement.style;
  if (config.primary) {
    const s = scaleFrom(config.primary);
    for (const k in s) root.setProperty(`--c-primary-${k}`, s[k]);
  }
  if (config.secondary) {
    const s = scaleFrom(config.secondary);
    for (const k in s) root.setProperty(`--c-secondary-${k}`, s[k]);
  }
  if (config.background) root.setProperty('--c-bg', triplet(config.background));
  if (config.font) {
    root.setProperty('--font-sans', `'${config.font}'`);
    root.setProperty('--font-heading', `'${config.font}'`);
  }
}

// Load the marketplace theme: apply the cached copy instantly (no flash of the
// default palette), then refresh from the public endpoint.
export async function loadBrand() {
  try {
    const cached = JSON.parse(localStorage.getItem('brand') || 'null');
    if (cached) { brand.value = cached; applyBrand(cached); }
  } catch {
    /* ignore */
  }
  try {
    const base = import.meta.env.VITE_API_URL || '/api/v1';
    const res = await fetch(`${base}/platform/theme/`);
    const config = (await res.json())?.data;
    if (config) {
      brand.value = config;
      applyBrand(config);
      localStorage.setItem('brand', JSON.stringify(config));
    }
  } catch {
    /* offline / not deployed yet — defaults from :root apply */
  }
}
