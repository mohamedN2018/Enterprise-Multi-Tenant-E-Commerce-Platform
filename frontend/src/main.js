import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import router from './router';
import { useAuthStore } from './stores/auth';
import { t, applyDir } from './i18n';
import { applyTheme, loadBrand } from './theme';

// Self-hosted fonts (bundled locally via @fontsource — no external CDN/link).
// Arabic-first: Cairo, Tajawal, Almarai; Latin: Roboto, Open Sans.
import '@fontsource/cairo/400.css';
import '@fontsource/cairo/500.css';
import '@fontsource/cairo/600.css';
import '@fontsource/cairo/700.css';
import '@fontsource/cairo/800.css';
import '@fontsource/cairo/900.css';
import '@fontsource/open-sans/400.css';
import '@fontsource/open-sans/500.css';
import '@fontsource/open-sans/600.css';
import '@fontsource/open-sans/700.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';
import '@fontsource/roboto/900.css';
import '@fontsource/tajawal/400.css';
import '@fontsource/tajawal/500.css';
import '@fontsource/tajawal/700.css';
import '@fontsource/tajawal/800.css';
import '@fontsource/tajawal/900.css';
import '@fontsource/almarai/400.css';
import '@fontsource/almarai/700.css';
import '@fontsource/almarai/800.css';
import './assets/main.css';

// Apply saved language (dir/lang) + theme before first paint.
applyDir();
applyTheme();
// Apply the marketplace brand theme (cached instantly, then refreshed).
loadBrand();

// Note: charts (apexcharts) are imported lazily inside the Dashboard page so the
// heavy charting library only ships in that route's chunk.
const app = createApp(App);
app.use(createPinia());
app.use(router);

// Global $t for templates ({{ $t('nav.home') }}).
app.config.globalProperties.$t = t;

// Restore the session (token -> profile) before the first route renders.
const auth = useAuthStore();
auth.bootstrap().finally(() => {
  app.mount('#app');
});
