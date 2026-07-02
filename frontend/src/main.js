import { createApp } from 'vue';
import { createPinia } from 'pinia';

import App from './App.vue';
import router from './router';
import { useAuthStore } from './stores/auth';
import { t, applyDir } from './i18n';
import { applyTheme } from './theme';
import './assets/main.css';

// Apply saved language (dir/lang) + theme before first paint.
applyDir();
applyTheme();

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
